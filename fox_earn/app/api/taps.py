from __future__ import annotations
import json
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ..database import get_db
from ..deps import get_current_user
from ..models import User, IdempotencyKey
from ..schemas import TapIn
from ..services import earning_service
from ..ratelimit import allow

router = APIRouter()


@router.post("/taps")
def post_taps(payload: TapIn, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    if not allow("taps", str(user.id), max_events=120, window_seconds=60):
        raise HTTPException(status_code=429, detail={"message": "Too many taps. Slow down.", "code": "rate_limited"})

    existing = db.query(IdempotencyKey).filter(
        IdempotencyKey.user_id == user.id, IdempotencyKey.key == payload.batch_id
    ).first()
    if existing:
        try:
            return json.loads(existing.response_json or "{}")
        except Exception:
            raise HTTPException(status_code=409, detail={"message": "Duplicate.", "code": "duplicate"})

    result = earning_service.process_taps(db, user, payload.taps)
    db.add(IdempotencyKey(user_id=user.id, key=payload.batch_id, response_json=json.dumps(result)))
    db.commit()
    return result
