from __future__ import annotations
from sqlalchemy.orm import Session
from ..models import User, Referral, ReferralClaim, Transaction
from ..settings_store import get_int


def process_referral(db: Session, new_user: User, referrer_telegram_id: int) -> None:
    if new_user.telegram_id == referrer_telegram_id:
        return
    referrer = db.query(User).filter(User.telegram_id == referrer_telegram_id).first()
    if referrer is None:
        return
    existing = db.query(Referral).filter(Referral.referred_id == new_user.id).first()
    if existing:
        return
    db.add(Referral(referrer_id=referrer.id, referred_id=new_user.id, status="valid"))
    new_user.referred_by_id = referrer.id
    db.commit()


def valid_count(db: Session, user: User) -> int:
    return db.query(Referral).filter(
        Referral.referrer_id == user.id, Referral.status == "valid"
    ).count()


def milestones_summary(db: Session, user: User) -> list:
    total = max(1, get_int(db, "referral_milestones_count", 10))
    reward_cents = max(0, get_int(db, "referral_reward_cents", 1000))
    min_valid = max(1, get_int(db, "referral_min_valid", 3))
    valid = valid_count(db, user)
    claims = db.query(ReferralClaim).filter(ReferralClaim.user_id == user.id).all()
    claimed_set = {c.milestone for c in claims}
    out = []
    for i in range(1, total + 1):
        out.append({
            "count": i,
            "reward_cents": reward_cents,
            "claimed": i in claimed_set,
            "qualified": valid >= i,
            "unlocked": valid >= min_valid,
        })
    return out


def claim_milestone(db: Session, user: User, milestone: int) -> dict:
    min_valid = max(1, get_int(db, "referral_min_valid", 3))
    total = max(1, get_int(db, "referral_milestones_count", 10))
    reward_cents = max(0, get_int(db, "referral_reward_cents", 1000))

    if milestone < 1 or milestone > total:
        return {"ok": False, "code": "bad_milestone", "message": "Invalid milestone."}

    valid = valid_count(db, user)
    if valid < min_valid:
        return {"ok": False, "code": "locked", "message": "You need " + str(min_valid) + " valid referrals to unlock claims."}
    if valid < milestone:
        return {"ok": False, "code": "not_qualified", "message": "Reach " + str(milestone) + " valid referrals first."}

    existing = db.query(ReferralClaim).filter(
        ReferralClaim.user_id == user.id, ReferralClaim.milestone == milestone
    ).first()
    if existing:
        return {"ok": False, "code": "already_claimed", "message": "Milestone already claimed."}

    user.dollar_balance_cents = (user.dollar_balance_cents or 0) + reward_cents
    db.add(ReferralClaim(user_id=user.id, milestone=milestone, reward_cents=reward_cents))
    db.add(Transaction(
        user_id=user.id, type="referral_claim",
        label="Referral milestone " + str(milestone),
        amount=reward_cents, unit="usd_cents", status="completed",
        ref="ref_claim_" + str(milestone),
    ))
    db.commit()
    db.refresh(user)
    return {"ok": True, "reward_cents": reward_cents, "balance_cents": int(user.dollar_balance_cents or 0)}
