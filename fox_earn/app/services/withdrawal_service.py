from __future__ import annotations
from datetime import datetime, timezone
from sqlalchemy.orm import Session
from ..models import User, Withdrawal, Transaction
from ..settings_store import get_int


def withdrawal_window_open(db: Session) -> bool:
    if not get_int(db, "withdrawal_enabled", 1):
        return False
    if not get_int(db, "withdrawal_timer_enabled", 0):
        return True
    target_ms = get_int(db, "withdrawal_target_utc_ms", 0)
    if target_ms <= 0:
        return True
    return int(datetime.now(timezone.utc).timestamp() * 1000) >= target_ms


def create_withdrawal(db: Session, user: User, amount_cents: int, method: str, destination: str) -> dict:
    if not get_int(db, "withdrawal_enabled", 1):
        return {"ok": False, "code": "disabled", "message": "Withdrawals are disabled."}
    if not user.wallet_active:
        return {"ok": False, "code": "no_wallet", "message": "Activate your wallet first."}
    if not withdrawal_window_open(db):
        return {"ok": False, "code": "window_closed", "message": "Withdrawal window is closed."}

    min_c = get_int(db, "min_withdrawal_cents", 500)
    max_c = get_int(db, "max_withdrawal_cents", 0)
    if amount_cents < min_c:
        return {"ok": False, "code": "below_min", "message": "Minimum withdrawal is $" + format(min_c/100, ".2f") + "."}
    if max_c and amount_cents > max_c:
        return {"ok": False, "code": "above_max", "message": "Maximum withdrawal is $" + format(max_c/100, ".2f") + "."}
    if amount_cents > user.withdrawable_cents:
        return {"ok": False, "code": "insufficient", "message": "Not enough withdrawable balance."}

    user.locked_cents = (user.locked_cents or 0) + amount_cents
    wd = Withdrawal(user_id=user.id, amount_cents=amount_cents, method=method, destination=destination, status="pending")
    db.add(wd)
    db.add(Transaction(user_id=user.id, type="withdrawal_reserve",
                       label="Reserved for withdrawal", amount=-amount_cents,
                       unit="usd_cents", status="pending"))
    db.commit(); db.refresh(wd)
    return {"ok": True, "id": wd.id, "status": wd.status}


def apply_admin_action(db: Session, wd_id: int, action: str, note: str = "") -> dict:
    wd = db.get(Withdrawal, wd_id)
    if wd is None:
        return {"ok": False, "message": "Not found."}
    user = db.get(User, wd.user_id)
    if user is None:
        return {"ok": False, "message": "User not found."}

    action = action.lower().strip()
    if action == "approve":
        if wd.status != "pending":
            return {"ok": False, "message": "Cannot approve a " + wd.status + " withdrawal."}
        wd.status = "approved"; wd.note = note
        db.commit()
        return {"ok": True, "status": wd.status}

    if action == "reject":
        if wd.status not in ("pending", "approved"):
            return {"ok": False, "message": "Cannot reject a " + wd.status + " withdrawal."}
        if wd.refunded:
            return {"ok": False, "message": "Already refunded."}
        user.locked_cents = max(0, (user.locked_cents or 0) - wd.amount_cents)
        wd.refunded = True; wd.status = "rejected"; wd.note = note
        db.add(Transaction(user_id=user.id, type="withdrawal_refund",
                           label="Refund for withdrawal #" + str(wd.id), amount=wd.amount_cents,
                           unit="usd_cents", status="completed"))
        db.commit()
        return {"ok": True, "status": wd.status}

    if action == "paid":
        if wd.status != "approved":
            return {"ok": False, "message": "Approve first."}
        user.locked_cents = max(0, (user.locked_cents or 0) - wd.amount_cents)
        user.dollar_balance_cents = max(0, (user.dollar_balance_cents or 0) - wd.amount_cents)
        wd.status = "paid"; wd.paid_at = datetime.now(timezone.utc); wd.note = note
        db.add(Transaction(user_id=user.id, type="withdrawal_paid",
                           label="Withdrawal #" + str(wd.id) + " paid", amount=0,
                           unit="usd_cents", status="completed"))
        db.commit()
        return {"ok": True, "status": wd.status}

    return {"ok": False, "message": "Unknown action " + action + "."}
