from __future__ import annotations
from datetime import datetime, timedelta, timezone
from sqlalchemy.orm import Session

from ..models import User, DepositRequest, Transaction
from ..settings_store import get_int


def create_deposit_request(db: Session, user: User) -> DepositRequest:
    minutes = max(1, get_int(db, "deposit_expiration_minutes", 15))
    expires_at = datetime.now(timezone.utc) + timedelta(minutes=minutes)
    dep = DepositRequest(
        user_id=user.id,
        status="awaiting_proof",
        expires_at=expires_at,
    )
    db.add(dep)
    db.commit()
    db.refresh(dep)
    return dep


def mark_expired_if_needed(db: Session, dep: DepositRequest) -> None:
    if dep.status == "awaiting_proof" and dep.expires_at:
        exp = dep.expires_at.replace(tzinfo=timezone.utc) if dep.expires_at.tzinfo is None else dep.expires_at
        if datetime.now(timezone.utc) > exp:
            dep.status = "expired"
            db.commit()


def submit_deposit(
    db: Session,
    dep: DepositRequest,
    amount: float,
    asset: str,
    network: str,
    tx_id: str,
    user_note: str,
    screenshot_path: str | None,
) -> DepositRequest:
    # Caller already validated ownership. Set fields.
    dep.amount = int(round(amount))
    dep.asset = asset[:16]
    dep.network = network[:32]
    dep.tx_id = tx_id[:128]
    dep.user_note = (user_note or "")[:2000]
    if screenshot_path:
        dep.screenshot_path = screenshot_path

    # Determine status: pending if within window, else needs_review (still reviewable)
    exp = dep.expires_at
    if exp is not None and exp.tzinfo is None:
        exp = exp.replace(tzinfo=timezone.utc)
    if exp is not None and datetime.now(timezone.utc) > exp:
        dep.status = "needs_review"
        dep.admin_note = "Proof submitted after expiry — please verify manually."
    else:
        dep.status = "pending"
    db.commit()
    db.refresh(dep)
    return dep


def admin_action(db: Session, dep_id: int, action: str, admin_telegram_id: int, note: str = "") -> dict:
    dep = db.get(DepositRequest, dep_id)
    if dep is None:
        return {"ok": False, "message": "Deposit not found."}
    user = db.get(User, dep.user_id)
    if user is None:
        return {"ok": False, "message": "User not found."}

    action = action.lower().strip()

    if action == "approve":
        if dep.status == "approved":
            return {"ok": False, "message": "Already approved."}
        if dep.status not in ("pending", "needs_review", "awaiting_proof"):
            return {"ok": False, "message": f"Cannot approve a {dep.status} deposit."}
        if dep.coins_credited and dep.coins_credited > 0:
            return {"ok": False, "message": "Already credited."}

        # Fixed conversion for now: 1 unit of asset = 1 coin * 100.
        # WARNING: This is a placeholder. The administrator must adjust
        # the coin conversion setting before enabling live deposits.
        rate = get_int(db, "deposit_coins_per_unit", 100)
        amount = int(dep.amount or 0)
        coins = amount * rate
        if coins <= 0:
            return {"ok": False, "message": "Deposit amount is zero or missing."}

        user.balance = (user.balance or 0) + coins
        user.total_earned = (user.total_earned or 0) + coins
        dep.status = "approved"
        dep.coins_credited = coins
        dep.admin_note = (note or "")[:2000]
        dep.reviewed_by_telegram_id = admin_telegram_id
        dep.reviewed_at = datetime.now(timezone.utc)
        db.add(Transaction(
            user_id=user.id, type="deposit_credit",
            label=f"Deposit #{dep.id} credited ({dep.amount} {dep.asset})",
            amount=coins, status="completed", ref=f"dep_{dep.id}",
        ))
        db.commit()
        return {"ok": True, "status": dep.status, "credited": coins}

    if action == "reject":
        if dep.status == "rejected":
            return {"ok": False, "message": "Already rejected."}
        dep.status = "rejected"
        dep.admin_note = (note or "Rejected by administrator")[:2000]
        dep.reviewed_by_telegram_id = admin_telegram_id
        dep.reviewed_at = datetime.now(timezone.utc)
        db.commit()
        return {"ok": True, "status": dep.status}

    if action == "needs_review":
        dep.status = "needs_review"
        if note:
            dep.admin_note = note[:2000]
        dep.reviewed_by_telegram_id = admin_telegram_id
        dep.reviewed_at = datetime.now(timezone.utc)
        db.commit()
        return {"ok": True, "status": dep.status}

    return {"ok": False, "message": f"Unknown action {action}."}
