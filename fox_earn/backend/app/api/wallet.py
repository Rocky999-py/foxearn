from __future__ import annotations
import base64
import binascii
import json
import re
import secrets
import time
from datetime import datetime, timezone
from pathlib import Path
from fastapi import APIRouter, Depends, HTTPException, Response
from sqlalchemy.orm import Session

from ..database import get_db
from ..deps import get_current_user
from ..models import User, Withdrawal, DepositRequest, IdempotencyKey
from ..schemas import WithdrawalIn, DepositSubmitIn
from ..services import withdrawal_service, deposit_service
from ..settings_store import get_int, get_setting
from ..config import get_settings

router = APIRouter()
settings = get_settings()

# Private storage — NOT mounted as public static
UPLOAD_ROOT = Path(__file__).resolve().parents[2] / "uploads"
DEPOSIT_DIR = UPLOAD_ROOT / "deposits"
DEPOSIT_DIR.mkdir(parents=True, exist_ok=True)

ALLOWED_TYPES = {"image/png": "png", "image/jpeg": "jpg", "image/jpg": "jpg", "image/webp": "webp"}

# Real file magic bytes — do not trust the client-supplied MIME alone
MAGIC = {
    b"\x89PNG\r\n\x1a\n": "image/png",
    b"\xff\xd8\xff": "image/jpeg",
}


def _detect_image_type(raw: bytes) -> str | None:
    if raw.startswith(b"\x89PNG\r\n\x1a\n"):
        return "image/png"
    if raw.startswith(b"\xff\xd8\xff"):
        return "image/jpeg"
    # WEBP: RIFF....WEBP
    if len(raw) >= 12 and raw[0:4] == b"RIFF" and raw[8:12] == b"WEBP":
        return "image/webp"
    return None


def _save_screenshot(data_url: str, user_id: int, max_bytes: int) -> str:
    m = re.match(r"^data:([^;]+);base64,(.+)$", data_url)
    if m:
        mime = m.group(1).lower()
        b64 = m.group(2)
    else:
        mime = "image/png"
        b64 = data_url

    if mime not in ALLOWED_TYPES:
        raise ValueError("Unsupported image type. Use PNG, JPG or WEBP.")

    try:
        raw = base64.b64decode(b64, validate=True)
    except (binascii.Error, ValueError):
        raise ValueError("Screenshot data is not valid base64.")

    if len(raw) > max_bytes:
        raise ValueError(f"Screenshot is too large (max {max_bytes // (1024*1024)} MB).")

    detected = _detect_image_type(raw)
    if detected is None:
        raise ValueError("File does not look like a real PNG/JPG/WEBP image.")

    ext = ALLOWED_TYPES[detected]
    filename = f"dep_{user_id}_{int(time.time())}_{secrets.token_hex(6)}.{ext}"
    with open(DEPOSIT_DIR / filename, "wb") as f:
        f.write(raw)
    return filename


def _parse_methods(raw: str) -> list:
    out = []
    for chunk in raw.split(","):
        chunk = chunk.strip()
        if not chunk or ":" not in chunk:
            continue
        code, label = chunk.split(":", 1)
        out.append({"code": code.strip(), "label": label.strip()})
    return out


def _deposit_to_dict(d: DepositRequest) -> dict:
    return {
        "id": d.id,
        "amount": d.amount,
        "asset": d.asset,
        "network": d.network,
        "method": d.method,
        "tx_id": d.tx_id,
        "status": d.status,
        "has_screenshot": bool(d.screenshot_path),
        "admin_note": d.admin_note,
        "created_at": d.created_at.isoformat() if d.created_at else None,
        "expires_at": d.expires_at.isoformat() if d.expires_at else None,
    }


@router.get("/wallet")
def get_wallet(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    min_w = get_int(db, "min_withdrawal", 5000)
    max_w = get_int(db, "max_withdrawal", 0)
    methods = _parse_methods(get_setting(db, "withdrawal_methods"))
    withdrawal_enabled = bool(get_int(db, "withdrawal_enabled", 1))
    deposit_enabled = bool(get_int(db, "deposit_enabled", 0))

    wds = db.query(Withdrawal).filter(Withdrawal.user_id == user.id).order_by(Withdrawal.created_at.desc()).limit(20).all()
    deps = db.query(DepositRequest).filter(DepositRequest.user_id == user.id).order_by(DepositRequest.created_at.desc()).limit(20).all()

    # Mark any expired deposits so the UI reflects reality
    for d in deps:
        deposit_service.mark_expired_if_needed(db, d)

    pending_deposits = db.query(DepositRequest).filter(
        DepositRequest.user_id == user.id,
        DepositRequest.status.in_(("awaiting_proof", "pending", "needs_review")),
    ).count()

    assets = [a.strip() for a in (get_setting(db, "deposit_assets") or "").split(",") if a.strip()]
    networks = [n.strip() for n in (get_setting(db, "deposit_networks") or "").split(",") if n.strip()]

    return {
        "summary": {
            "balance": int(user.balance or 0),
            "withdrawable": int(user.withdrawable),
            "locked": int(user.locked or 0),
            "pending_deposits": int(pending_deposits),
        },
        "min_withdrawal": min_w,
        "max_withdrawal": max_w,
        "withdrawal_enabled": withdrawal_enabled,
        "deposit_enabled": deposit_enabled,
        "eligible": (user.withdrawable >= min_w) and bool(methods) and withdrawal_enabled,
        "methods": methods,
        "requirements": [
            {"label": f"Reach {min_w} withdrawable coins", "met": user.withdrawable >= min_w},
            {"label": "Withdrawals enabled", "met": withdrawal_enabled},
        ],
        "deposit_min": get_int(db, "deposit_min", 10),
        "deposit_max": get_int(db, "deposit_max", 10000),
        "deposit_assets": assets,
        "deposit_networks": networks,
        "deposit_instructions": get_setting(db, "deposit_instructions"),
        "deposit_binance_pay_id": get_setting(db, "deposit_binance_pay_id"),
        "requests": [
            {
                "id": w.id, "amount": w.amount, "method": w.method,
                "status": w.status,
                "created_at": w.created_at.isoformat() if w.created_at else None,
            } for w in wds
        ],
        "deposits": [_deposit_to_dict(d) for d in deps],
    }


@router.post("/withdrawals")
def create_withdrawal(payload: WithdrawalIn, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    if not get_int(db, "withdrawal_enabled", 1):
        raise HTTPException(status_code=400, detail={"message": "Withdrawals are disabled.", "code": "withdrawals_disabled"})

    if payload.idempotency_key:
        existing = db.query(IdempotencyKey).filter(
            IdempotencyKey.user_id == user.id, IdempotencyKey.key == payload.idempotency_key
        ).first()
        if existing:
            try:
                return json.loads(existing.response_json or "{}")
            except Exception:
                pass

    result = withdrawal_service.create_withdrawal(db, user, payload.amount, payload.method, payload.destination)
    if not result.get("ok"):
        raise HTTPException(status_code=400, detail={"message": result["message"], "code": result.get("code", "withdrawal_error")})

    response = {"id": result["id"], "status": result["status"]}
    if payload.idempotency_key:
        db.add(IdempotencyKey(user_id=user.id, key=payload.idempotency_key, response_json=json.dumps(response)))
        db.commit()
    return response


# ============ DEPOSITS ============

@router.post("/deposits/start")
def deposits_start(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    if not get_int(db, "deposit_enabled", 0):
        raise HTTPException(status_code=400, detail={"message": "Deposits are disabled.", "code": "deposits_disabled"})

    # Cancel any prior awaiting_proof requests for this user
    for old in db.query(DepositRequest).filter(
        DepositRequest.user_id == user.id, DepositRequest.status == "awaiting_proof"
    ).all():
        old.status = "cancelled"
    db.commit()

    dep = deposit_service.create_deposit_request(db, user)
    minutes = max(1, get_int(db, "deposit_expiration_minutes", 15))
    expires_at = dep.expires_at
    if expires_at and expires_at.tzinfo is None:
        expires_at = expires_at.replace(tzinfo=timezone.utc)
    remaining = max(0, int((expires_at - datetime.now(timezone.utc)).total_seconds())) if expires_at else minutes * 60

    return {
        "id": dep.id,
        "status": dep.status,
        "expires_at": dep.expires_at.isoformat() if dep.expires_at else None,
        "expires_in_seconds": remaining,
    }


@router.post("/deposits/{dep_id}/submit")
def deposits_submit(dep_id: int, payload: DepositSubmitIn, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    dep = db.get(DepositRequest, dep_id)
    if dep is None or dep.user_id != user.id:
        raise HTTPException(status_code=404, detail={"message": "Deposit not found.", "code": "not_found"})
    if dep.status not in ("awaiting_proof", "expired"):
        raise HTTPException(status_code=400, detail={"message": f"Cannot submit in status {dep.status}.", "code": "bad_state"})

    max_mb = max(1, get_int(db, "screenshot_max_mb", 5))
    max_bytes = max_mb * 1024 * 1024

    screenshot_filename = None
    if payload.screenshot_base64:
        try:
            screenshot_filename = _save_screenshot(payload.screenshot_base64, user.id, max_bytes)
        except ValueError as e:
            raise HTTPException(status_code=400, detail={"message": str(e), "code": "bad_screenshot"})

    dep = deposit_service.submit_deposit(
        db, dep,
        amount=payload.amount, asset=payload.asset, network=payload.network,
        tx_id=payload.tx_id, user_note=payload.user_note or "",
        screenshot_path=screenshot_filename,
    )
    return _deposit_to_dict(dep)


@router.post("/deposits/{dep_id}/cancel")
def deposits_cancel(dep_id: int, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    dep = db.get(DepositRequest, dep_id)
    if dep is None or dep.user_id != user.id:
        raise HTTPException(status_code=404, detail={"message": "Deposit not found.", "code": "not_found"})
    if dep.status in ("awaiting_proof", "expired"):
        dep.status = "cancelled"
        db.commit()
    return {"id": dep.id, "status": dep.status}


@router.get("/deposits/{dep_id}/screenshot")
def deposits_screenshot(dep_id: int, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    dep = db.get(DepositRequest, dep_id)
    if dep is None:
        raise HTTPException(status_code=404, detail={"message": "Deposit not found.", "code": "not_found"})

    is_admin = user.telegram_id in settings.admin_ids
    if dep.user_id != user.id and not is_admin:
        raise HTTPException(status_code=403, detail={"message": "Not allowed.", "code": "forbidden"})

    if not dep.screenshot_path:
        raise HTTPException(status_code=404, detail={"message": "No screenshot.", "code": "no_screenshot"})

    path = DEPOSIT_DIR / dep.screenshot_path
    if not path.exists():
        raise HTTPException(status_code=404, detail={"message": "File missing.", "code": "file_missing"})

    ext = path.suffix.lower()
    mime = "image/png" if ext == ".png" else "image/webp" if ext == ".webp" else "image/jpeg"
    data = path.read_bytes()
    return Response(content=data, media_type=mime, headers={"Cache-Control": "private, max-age=60"})
