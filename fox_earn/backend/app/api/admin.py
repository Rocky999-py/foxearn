from __future__ import annotations
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func
from sqlalchemy.orm import Session

from ..database import get_db
from ..deps import get_current_user
from ..models import User, Withdrawal, Task, TaskCompletion, Setting, AuditLog, DepositRequest
from ..schemas import AdminWithdrawalAction, AdminDepositAction
from ..security.permissions import require_admin
from ..services import withdrawal_service, audit_service, deposit_service

router = APIRouter()


@router.get("/admin/overview")
def overview(admin: User = Depends(require_admin), db: Session = Depends(get_db)):
    total_users = db.query(func.count(User.id)).scalar() or 0
    total_coins = db.query(func.coalesce(func.sum(User.balance), 0)).scalar() or 0
    pending_w = db.query(func.count(Withdrawal.id)).filter(Withdrawal.status == "pending").scalar() or 0
    pending_d = db.query(func.count(DepositRequest.id)).filter(DepositRequest.status == "pending").scalar() or 0
    pending_t = db.query(func.count(TaskCompletion.id)).filter(TaskCompletion.status == "pending").scalar() or 0
    return {
        "stats": {
            "total_users": int(total_users),
            "total_coins": int(total_coins),
            "pending_withdrawals": int(pending_w),
            "pending_deposits": int(pending_d),
            "pending_task_reviews": int(pending_t),
            "active_today": 0,
        }
    }


# ---------- DEPOSITS ----------
@router.get("/admin/deposits")
def list_deposits(
    status: str = Query(default="pending"),
    limit: int = Query(default=50, ge=1, le=200),
    admin: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    q = db.query(DepositRequest)
    if status:
        q = q.filter(DepositRequest.status == status)
    rows = q.order_by(DepositRequest.created_at.desc()).limit(limit).all()
    out = []
    for d in rows:
        u = db.get(User, d.user_id)
        out.append({
            "id": d.id,
            "amount": d.amount,
            "asset": d.asset,
            "network": d.network,
            "method": d.method,
            "tx_id": d.tx_id,
            "status": d.status,
            "user_note": d.user_note,
            "admin_note": d.admin_note,
            "coins_credited": int(d.coins_credited or 0),
            "display_name": u.display_name if u else "User",
            "has_screenshot": bool(d.screenshot_path),
            "created_at": d.created_at.isoformat() if d.created_at else None,
            "expires_at": d.expires_at.isoformat() if d.expires_at else None,
        })
    return {"deposits": out}


@router.post("/admin/deposits/{dep_id}/action")
def action_deposit(
    dep_id: int,
    payload: AdminDepositAction,
    admin: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    result = deposit_service.admin_action(db, dep_id, payload.action, admin.telegram_id, payload.note or "")
    if not result.get("ok"):
        raise HTTPException(status_code=400, detail={"message": result["message"], "code": "deposit_action_failed"})
    audit_service.log(db, f"deposit_{payload.action}",
                      actor=admin.display_name, actor_telegram_id=admin.telegram_id,
                      details={"deposit_id": dep_id, "note": payload.note})
    return result


# ---------- WITHDRAWALS ----------
@router.get("/admin/withdrawals")
def list_withdrawals(
    status: str = Query(default="pending"),
    limit: int = Query(default=50, ge=1, le=200),
    admin: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    q = db.query(Withdrawal)
    if status:
        q = q.filter(Withdrawal.status == status)
    rows = q.order_by(Withdrawal.created_at.desc()).limit(limit).all()
    out = []
    for w in rows:
        u = db.get(User, w.user_id)
        out.append({
            "id": w.id,
            "amount": w.amount,
            "method": w.method,
            "destination": w.destination,
            "status": w.status,
            "display_name": u.display_name if u else "User",
            "created_at": w.created_at.isoformat() if w.created_at else None,
            "has_screenshot": bool(w.screenshot_path),
        })
    return {"withdrawals": out}


@router.post("/admin/withdrawals/{wid}/action")
def action_withdrawal(
    wid: int,
    payload: AdminWithdrawalAction,
    admin: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    result = withdrawal_service.apply_admin_action(db, wid, payload.action, payload.note or "")
    if not result.get("ok"):
        raise HTTPException(status_code=400, detail={"message": result["message"], "code": "withdrawal_action_failed"})
    audit_service.log(db, f"withdrawal_{payload.action}",
                      actor=admin.display_name, actor_telegram_id=admin.telegram_id,
                      details={"withdrawal_id": wid, "note": payload.note})
    return result


# ---------- TASKS / SETTINGS / AUDIT ----------
@router.get("/admin/tasks")
def list_tasks(admin: User = Depends(require_admin), db: Session = Depends(get_db)):
    rows = db.query(Task).order_by(Task.id.desc()).all()
    return {"tasks": [{"id": t.id, "title": t.title, "description": t.description or "", "reward": t.reward, "verification_type": t.verification_type, "is_active": bool(t.is_active)} for t in rows]}


@router.get("/admin/settings")
def list_settings(admin: User = Depends(require_admin), db: Session = Depends(get_db)):
    rows = db.query(Setting).order_by(Setting.key.asc()).all()
    return {"settings": [{"key": r.key, "value": r.value} for r in rows]}


@router.get("/admin/audit")
def list_audit(limit: int = Query(default=50, ge=1, le=200), admin: User = Depends(require_admin), db: Session = Depends(get_db)):
    rows = db.query(AuditLog).order_by(AuditLog.created_at.desc()).limit(limit).all()
    return {"logs": [{"id": r.id, "action": r.action, "actor": r.actor or "system", "created_at": r.created_at.isoformat() if r.created_at else None} for r in rows]}
