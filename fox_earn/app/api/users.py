from __future__ import annotations
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from ..database import get_db
from ..deps import get_current_user
from ..models import User
from ..services import referral_service
from ..settings_store import get_int
from ..config import get_settings

router = APIRouter()
settings = get_settings()


@router.get("/profile")
def get_profile(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    valid = referral_service.valid_count(db, user)
    return {
        "user": {
            "telegram_id": user.telegram_id,
            "display_name": user.display_name,
            "username": user.username,
            "photo_url": user.photo_url,
            "created_at": user.created_at.isoformat() if user.created_at else None,
        },
        "stats": {
            "balance": int(user.balance or 0),
            "dollar_balance_cents": int(user.dollar_balance_cents or 0),
            "withdrawable_cents": int(user.withdrawable_cents),
            "locked_cents": int(user.locked_cents or 0),
            "total_earned": int(user.total_earned or 0),
            "valid_referrals": valid,
        },
        "wallet_active": bool(user.wallet_active),
        "is_admin": user.telegram_id in settings.admin_ids,
    }
