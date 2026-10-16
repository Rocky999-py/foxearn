from __future__ import annotations
from sqlalchemy.orm import Session
from ..models import User, Transaction
from ..settings_store import get_int


def process_taps(db: Session, user: User, taps: int) -> dict:
    coins_per_tap = max(1, get_int(db, "coins_per_tap", 1))
    reward = taps * coins_per_tap

    user.balance = (user.balance or 0) + reward
    user.total_earned = (user.total_earned or 0) + reward

    db.add(Transaction(
        user_id=user.id, type="tap_reward",
        label="Tap reward (" + str(taps) + ")",
        amount=reward, unit="coins", status="completed",
    ))
    db.commit()
    db.refresh(user)

    return {
        "accepted": taps,
        "balance": int(user.balance or 0),
        "dollar_balance_cents": int(user.dollar_balance_cents or 0),
        "total_earned": int(user.total_earned or 0),
    }
