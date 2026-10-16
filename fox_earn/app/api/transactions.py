from __future__ import annotations
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from ..database import get_db
from ..deps import get_current_user
from ..models import User, Transaction

router = APIRouter()


@router.get("/transactions")
def list_transactions(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
):
    rows = db.query(Transaction).filter(Transaction.user_id == user.id)\
        .order_by(Transaction.created_at.desc()).offset(offset).limit(limit).all()
    return {
        "transactions": [
            {
                "id": t.id,
                "type": t.type,
                "label": t.label,
                "amount": int(t.amount),
                "unit": t.unit or "coins",
                "status": t.status,
                "created_at": t.created_at.isoformat() if t.created_at else None,
            }
            for t in rows
        ]
    }
