from __future__ import annotations
from datetime import datetime, timezone
from sqlalchemy.orm import Session
from ..models import User, WalletActivationRequest
from ..settings_store import get_int, get_setting


def methods_configured(db: Session) -> list:
    out = []
    for code, label in (("okx", "OKX"), ("bybit", "Bybit"), ("binance", "Binance")):
        if get_int(db, "wallet_method_" + code + "_enabled", 1):
            out.append({
                "code": code,
                "label": label,
                "fee_cents": get_int(db, "wallet_activation_fee_cents", 2000),
                "instructions": get_setting(db, "wallet_instr_" + code),
                "destination": get_setting(db, "wallet_dest_" + code),
            })
    return out


def create_request(db: Session, user: User, method: str, screenshot_path, tx_ref: str) -> WalletActivationRequest:
    fee = get_int(db, "wallet_activation_fee_cents", 2000)
    req = WalletActivationRequest(
        user_id=user.id, method=method, fee_cents=fee,
        tx_ref=tx_ref[:128] if tx_ref else None,
        screenshot_path=screenshot_path, status="pending",
    )
    db.add(req); db.commit(); db.refresh(req)
    return req


def admin_action(db: Session, req_id: int, action: str, admin_telegram_id: int, note: str = "") -> dict:
    req = db.get(WalletActivationRequest, req_id)
    if req is None:
        return {"ok": False, "message": "Request not found."}
    user = db.get(User, req.user_id)
    if user is None:
        return {"ok": False, "message": "User not found."}

    action = action.lower().strip()

    if action == "approve":
        if req.status == "approved":
            return {"ok": False, "message": "Already approved."}
        req.status = "approved"
        req.admin_note = (note or "")[:2000]
        req.reviewed_by_telegram_id = admin_telegram_id
        req.reviewed_at = datetime.now(timezone.utc)
        user.wallet_active = True
        user.wallet_activated_at = datetime.now(timezone.utc)
        db.commit()
        return {"ok": True, "status": req.status}

    if action == "reject":
        if req.status == "rejected":
            return {"ok": False, "message": "Already rejected."}
        req.status = "rejected"
        req.admin_note = (note or "Rejected")[:2000]
        req.reviewed_by_telegram_id = admin_telegram_id
        req.reviewed_at = datetime.now(timezone.utc)
        db.commit()
        return {"ok": True, "status": req.status}

    return {"ok": False, "message": "Unknown action " + action + "."}
