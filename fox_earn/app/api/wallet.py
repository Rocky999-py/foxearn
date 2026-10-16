from __future__ import annotations
import base64
import binascii
import json
import re
import secrets
import time
from pathlib import Path
from fastapi import APIRouter, Depends, HTTPException, Response
from sqlalchemy.orm import Session

from ..database import get_db
from ..deps import get_current_user
from ..models import User, Withdrawal, WalletActivationRequest, IdempotencyKey
from ..schemas import WithdrawalIn, WalletActivationSubmitIn
from ..services import withdrawal_service, wallet_activation_service
from ..settings_store import get_int, get_setting
from ..config import get_settings

router = APIRouter()
settings = get_settings()

UPLOAD_ROOT = Path(__file__).resolve().parents[2] / "uploads"
WALLET_DIR = UPLOAD_ROOT / "wallet"
WALLET_DIR.mkdir(parents=True, exist_ok=True)


def _detect_image_type(raw: bytes):
    if raw.startswith(b"\x89PNG\r\n\x1a\n"):
        return "image/png"
    if raw.startswith(b"\xff\xd8\xff"):
        return "image/jpeg"
    if len(raw) >= 12 and raw[0:4] == b"RIFF" and raw[8:12] == b"WEBP":
        return "image/webp"
    return None


def _save(data_url: str, user_id: int, max_mb: int) -> str:
    m = re.match(r"^data:([^;]+);base64,(.+)$", data_url)
    if m:
        mime, b64 = m.group(1).lower(), m.group(2)
    else:
        mime, b64 = "image/png", data_url
    if mime not in ("image/png", "image/jpeg", "image/jpg", "image/webp"):
        raise ValueError("Unsupported image type.")
    try:
        raw = base64.b64decode(b64, validate=True)
    except (binascii.Error, ValueError):
        raise ValueError("Invalid base64.")
    if len(raw) > max_mb * 1024 * 1024:
        raise ValueError("Image exceeds " + str(max_mb) + " MB.")
    detected = _detect_image_type(raw)
    if not detected:
        raise ValueError("File does not look like PNG/JPG/WEBP.")
    ext = {"image/png": "png", "image/jpeg": "jpg", "image/webp": "webp"}[detected]
    fn = "wa_" + str(user_id) + "_" + str(int(time.time())) + "_" + secrets.token_hex(6) + "." + ext
    with open(WALLET_DIR / fn, "wb") as f:
        f.write(raw)
    return fn


def _parse_methods(raw: str):
    out = []
    for chunk in raw.split(","):
        chunk = chunk.strip()
        if not chunk or ":" not in chunk:
            continue
        c, l = chunk.split(":", 1)
        out.append({"code": c.strip(), "label": l.strip()})
    return out


@router.get("/wallet")
def get_wallet(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    wallet_enabled = bool(get_int(db, "wallet_activation_enabled", 0))
    fee_cents = get_int(db, "wallet_activation_fee_cents", 2000)
    withdrawal_methods = _parse_methods(get_setting(db, "withdrawal_methods"))

    activations = db.query(WalletActivationRequest)\
        .filter(WalletActivationRequest.user_id == user.id)\
        .order_by(WalletActivationRequest.created_at.desc()).limit(20).all()

    withdrawals = db.query(Withdrawal)\
        .filter(Withdrawal.user_id == user.id)\
        .order_by(Withdrawal.created_at.desc()).limit(20).all()

    timer_enabled = bool(get_int(db, "withdrawal_timer_enabled", 0))
    target_ms = get_int(db, "withdrawal_target_utc_ms", 0)
    open_now = withdrawal_service.withdrawal_window_open(db)

    return {
        "summary": {
            "balance": int(user.balance or 0),
            "dollar_balance_cents": int(user.dollar_balance_cents or 0),
            "withdrawable_cents": int(user.withdrawable_cents),
            "locked_cents": int(user.locked_cents or 0),
        },
        "wallet_active": bool(user.wallet_active),
        "wallet_enabled": wallet_enabled,
        "wallet_fee_cents": fee_cents,
        "wallet_methods": wallet_activation_service.methods_configured(db) if wallet_enabled else [],
        "wallet_activations": [
            {
                "id": a.id, "method": a.method, "fee_cents": a.fee_cents,
                "status": a.status, "admin_note": a.admin_note,
                "has_screenshot": bool(a.screenshot_path),
                "created_at": a.created_at.isoformat() if a.created_at else None,
            } for a in activations
        ],
        "min_withdrawal_cents": get_int(db, "min_withdrawal_cents", 500),
        "max_withdrawal_cents": get_int(db, "max_withdrawal_cents", 0),
        "withdrawal_methods": withdrawal_methods,
        "withdrawals": [
            {
                "id": w.id, "amount_cents": w.amount_cents, "method": w.method,
                "status": w.status,
                "created_at": w.created_at.isoformat() if w.created_at else None,
            } for w in withdrawals
        ],
        "withdrawal_timer_enabled": timer_enabled,
        "withdrawal_target_ms": target_ms,
        "withdrawal_open": open_now,
    }


@router.post("/wallet/activate/submit")
def wallet_activate_submit(payload: WalletActivationSubmitIn, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    if not get_int(db, "wallet_activation_enabled", 0):
        raise HTTPException(status_code=400, detail={"message": "Add Wallet is locked.", "code": "locked"})
    if payload.method not in ("okx", "bybit", "binance"):
        raise HTTPException(status_code=400, detail={"message": "Unknown method.", "code": "bad_method"})
    if not get_int(db, "wallet_method_" + payload.method + "_enabled", 1):
        raise HTTPException(status_code=400, detail={"message": "Method disabled.", "code": "method_disabled"})

    max_mb = max(1, get_int(db, "screenshot_max_mb", 5))
    try:
        filename = _save(payload.screenshot_base64, user.id, max_mb)
    except ValueError as e:
        raise HTTPException(status_code=400, detail={"message": str(e), "code": "bad_screenshot"})

    req = wallet_activation_service.create_request(db, user, payload.method, filename, payload.tx_ref or "")
    return {"id": req.id, "status": req.status}


@router.get("/wallet/activate/{req_id}/screenshot")
def wallet_activation_screenshot(req_id: int, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    req = db.get(WalletActivationRequest, req_id)
    if req is None:
        raise HTTPException(status_code=404, detail={"message": "Not found.", "code": "not_found"})
    is_admin = user.telegram_id in settings.admin_ids
    if req.user_id != user.id and not is_admin:
        raise HTTPException(status_code=403, detail={"message": "Forbidden.", "code": "forbidden"})
    if not req.screenshot_path:
        raise HTTPException(status_code=404, detail={"message": "No screenshot.", "code": "no_screenshot"})
    path = WALLET_DIR / req.screenshot_path
    if not path.exists():
        raise HTTPException(status_code=404, detail={"message": "Missing file.", "code": "file_missing"})
    ext = path.suffix.lower()
    mime = "image/png" if ext == ".png" else "image/webp" if ext == ".webp" else "image/jpeg"
    return Response(content=path.read_bytes(), media_type=mime, headers={"Cache-Control": "private, max-age=60"})


@router.post("/withdrawals")
def create_withdrawal(payload: WithdrawalIn, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    if payload.idempotency_key:
        existing = db.query(IdempotencyKey).filter(
            IdempotencyKey.user_id == user.id, IdempotencyKey.key == payload.idempotency_key
        ).first()
        if existing:
            try:
                return json.loads(existing.response_json or "{}")
            except Exception:
                pass

    result = withdrawal_service.create_withdrawal(db, user, payload.amount_cents, payload.method, payload.destination)
    if not result.get("ok"):
        raise HTTPException(status_code=400, detail={"message": result["message"], "code": result.get("code", "withdrawal_error")})

    response = {"id": result["id"], "status": result["status"]}
    if payload.idempotency_key:
        db.add(IdempotencyKey(user_id=user.id, key=payload.idempotency_key, response_json=json.dumps(response)))
        db.commit()
    return response
