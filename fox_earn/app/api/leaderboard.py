from __future__ import annotations
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from ..database import get_db
from ..deps import get_current_user
from ..models import User

router = APIRouter()


@router.get("/leaderboard")
def get_leaderboard(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
):
    rows = db.query(User).filter(User.is_banned == False)\
        .order_by(User.total_earned.desc()).offset(offset).limit(limit).all()
    return {
        "leaderboard": [
            {
                "rank": offset + i + 1,
                "display_name": r.display_name,
                "total_earned": int(r.total_earned or 0),
                "balance": int(r.balance or 0),
            }
            for i, r in enumerate(rows)
        ]
    }
