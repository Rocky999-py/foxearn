from __future__ import annotations
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func
from sqlalchemy.orm import Session

from ..database import get_db
from ..deps import get_current_user
from ..models import User, Withdrawal, WalletActivationRequest, Setting, AuditLog
from ..schemas import AdminWithdrawalAction, AdminWalletActivationAction, AdminSettingsPatch, AdminTimerIn
from ..security.permissions import require_admin
from ..services import withdrawal_service, wallet_activation_service, audit_service
from ..settings_store import set_setting

router = APIRouter()


@router.get("/admin/overview")
def overview(admin: User = Depends(require_admin), db: Session = Depends(get_db)):
    total_users = db.query(func.count(User.id)).scalar() or 0
    total_coins = db.query(func.coalesce(func.sum(User.balance), 0)).scalar() or 0
    total_usd = db.query(func.coalesce(func.sum(User.dollar_balance_cents), 0)).scalar() or 0
    pending_w = db.query(func.count(Withdrawal.id)).filter(Withdrawal.status == "pending").scalar() or 0
    pending_a = db.query(func.count(WalletActivationRequest.id)).filter(WalletActivationRequest.status == "pending").scalar() or 0
    return {"stats": {
        "total_users": int(total_users),
        "total_coins": int(total_coins),
        "total_dollar_cents": int(total_usd),
        "pending_wallet_activations": int(pending_a),
        "pending_withdrawals": int(pending_w),
    }}


@router.get("/admin/wallet-activations")
def list_activations(status: str = Query(default="pending"), limit: int = Query(default=50, ge=1, le=200),
                     admin: User = Depends(require_admin), db: Session = Depends(get_db)):
    q = db.query(WalletActivationRequest)
    if status:
        q = q.filter(WalletActivationRequest.status == status)
    rows = q.order_by(WalletActivationRequest.created_at.desc()).limit(limit).all()
    out = []
    for a in rows:
        u = db.get(User, a.user_id)
        out.append({
            "id": a.id, "method": a.method, "fee_cents": a.fee_cents,
            "tx_ref": a.tx_ref, "status": a.status, "admin_note": a.admin_note,
            "display_name": u.display_name if u else "User",
            "has_screenshot": bool(a.screenshot_path),
            "created_at": a.created_at.isoformat() if a.created_at else None,
        })
    return {"activations": out}


@router.post("/admin/wallet-activations/{rid}/action")
def activation_action(rid: int, payload: AdminWalletActivationAction,
                     admin: User = Depends(require_admin), db: Session = Depends(get_db)):
    result = wallet_activation_service.admin_action(db, rid, payload.action, admin.telegram_id, payload.note or "")
    if not result.get("ok"):
        raise HTTPException(status_code=400, detail={"message": result["message"], "code": "activation_failed"})
    audit_service.log(db, "wallet_activation_" + payload.action,
                      actor=admin.display_name, actor_telegram_id=admin.telegram_id,
                      details={"id": rid, "note": payload.note})
    return result


@router.get("/admin/withdrawals")
def list_withdrawals(status: str = Query(default="pending"), limit: int = Query(default=50, ge=1, le=200),
                     admin: User = Depends(require_admin), db: Session = Depends(get_db)):
    q = db.query(Withdrawal)
    if status:
        q = q.filter(Withdrawal.status == status)
    rows = q.order_by(Withdrawal.created_at.desc()).limit(limit).all()
    out = []
    for w in rows:
        u = db.get(User, w.user_id)
        out.append({
            "id": w.id, "amount_cents": w.amount_cents, "method": w.method,
            "destination": w.destination, "status": w.status,
            "display_name": u.display_name if u else "User",
            "created_at": w.created_at.isoformat() if w.created_at else None,
        })
    return {"withdrawals": out}


@router.post("/admin/withdrawals/{wid}/action")
def withdrawal_action(wid: int, payload: AdminWithdrawalAction,
                      admin: User = Depends(require_admin), db: Session = Depends(get_db)):
    result = withdrawal_service.apply_admin_action(db, wid, payload.action, payload.note or "")
    if not result.get("ok"):
        raise HTTPException(status_code=400, detail={"message": result["message"], "code": "withdrawal_failed"})
    audit_service.log(db, "withdrawal_" + payload.action,
                      actor=admin.display_name, actor_telegram_id=admin.telegram_id,
                      details={"id": wid, "note": payload.note})
    return result


@router.post("/admin/withdrawal-timer")
def set_withdrawal_timer(payload: AdminTimerIn, admin: User = Depends(require_admin), db: Session = Depends(get_db)):
    target_ms = 0
    if payload.target_local:
        try:
            dt_local = datetime.fromisoformat(payload.target_local)
            if dt_local.tzinfo is None:
                dt_local = dt_local.replace(tzinfo=timezone.utc)
            target_ms = int(dt_local.timestamp() * 1000)
        except Exception:
            raise HTTPException(status_code=400, detail={"message": "Invalid datetime.", "code": "bad_datetime"})
    set_setting(db, "withdrawal_timer_enabled", "1" if payload.enabled else "0")
    set_setting(db, "withdrawal_target_local", payload.target_local or "")
    set_setting(db, "withdrawal_target_utc_ms", str(target_ms))
    audit_service.log(db, "withdrawal_timer_set", actor=admin.display_name,
                      actor_telegram_id=admin.telegram_id,
                      details={"target": payload.target_local, "enabled": payload.enabled})
    return {"ok": True, "target_ms": target_ms, "enabled": payload.enabled}


@router.post("/admin/settings")
def patch_settings(payload: AdminSettingsPatch, admin: User = Depends(require_admin), db: Session = Depends(get_db)):
    allowed = {
        "wallet_activation_enabled", "wallet_activation_fee_cents",
        "wallet_method_okx_enabled", "wallet_method_bybit_enabled", "wallet_method_binance_enabled",
        "wallet_instr_okx", "wallet_instr_bybit", "wallet_instr_binance",
        "wallet_dest_okx", "wallet_dest_bybit", "wallet_dest_binance",
        "referral_min_valid", "referral_milestones_count", "referral_reward_cents",
        "withdrawal_enabled", "min_withdrawal_cents", "max_withdrawal_cents",
        "withdrawal_methods", "screenshot_max_mb", "maintenance_mode",
    }
    changed = {}
    for k, v in (payload.updates or {}).items():
        if k not in allowed:
            continue
        set_setting(db, k, str(v))
        changed[k] = str(v)
    audit_service.log(db, "settings_patch", actor=admin.display_name,
                      actor_telegram_id=admin.telegram_id, details=changed)
    return {"ok": True, "updated": list(changed.keys())}


@router.get("/admin/settings")
def list_settings(admin: User = Depends(require_admin), db: Session = Depends(get_db)):
    rows = db.query(Setting).order_by(Setting.key.asc()).all()
    return {"settings": [{"key": r.key, "value": r.value} for r in rows]}


@router.get("/admin/audit")
def list_audit(limit: int = Query(default=50, ge=1, le=200),
               admin: User = Depends(require_admin), db: Session = Depends(get_db)):
    rows = db.query(AuditLog).order_by(AuditLog.created_at.desc()).limit(limit).all()
    return {"logs": [{"id": r.id, "action": r.action, "actor": r.actor or "system",
                      "created_at": r.created_at.isoformat() if r.created_at else None} for r in rows]}