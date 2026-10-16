from __future__ import annotations
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ..database import get_db
from ..deps import get_current_user
from ..models import User
from ..schemas import ReferralClaimIn
from ..services import referral_service
from ..settings_store import get_int
from ..config import get_settings

router = APIRouter()
settings = get_settings()


@router.get("/referrals")
def get_referrals(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    valid = referral_service.valid_count(db, user)
    link = "https://t.me/" + settings.bot_username + "?start=ref_" + str(user.telegram_id)
    return {
        "referral_link": link,
        "valid_referrals": valid,
        "min_referrals_to_unlock": max(1, get_int(db, "referral_min_valid", 3)),
        "milestones": referral_service.milestones_summary(db, user),
    }


@router.post("/referrals/claim")
def claim(payload: ReferralClaimIn, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    result = referral_service.claim_milestone(db, user, payload.milestone)
    if not result.get("ok"):
        raise HTTPException(status_code=400, detail={"message": result["message"], "code": result.get("code", "claim_error")})
    return result
