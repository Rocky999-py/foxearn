from __future__ import annotations
import time
from typing import Optional
from fastapi import Depends, Header, HTTPException, status
from sqlalchemy.orm import Session

from .database import get_db
from .models import User, SessionToken


def get_current_user(
    authorization: Optional[str] = Header(default=None),
    db: Session = Depends(get_db),
) -> User:
    if not authorization or not authorization.lower().startswith("bearer "):
        raise HTTPException(status_code=401, detail={"message": "Missing bearer token.", "code": "no_token"})
    token = authorization.split(" ", 1)[1].strip()
    row = db.query(SessionToken).filter(SessionToken.token == token).first()
    if row is None:
        raise HTTPException(status_code=401, detail={"message": "Invalid session token.", "code": "bad_token"})
    now = int(time.time())
    if row.expires_at < now:
        db.delete(row); db.commit()
        raise HTTPException(status_code=401, detail={"message": "Session expired.", "code": "expired_token"})
    user = db.get(User, row.user_id)
    if user is None or user.is_banned:
        raise HTTPException(status_code=401, detail={"message": "User not available.", "code": "no_user"})
    return user
