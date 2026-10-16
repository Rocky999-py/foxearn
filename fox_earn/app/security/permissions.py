from __future__ import annotations
from fastapi import Depends, HTTPException, status
from ..deps import get_current_user
from ..models import User
from ..config import get_settings

settings = get_settings()


def require_admin(user: User = Depends(get_current_user)) -> User:
    if user.telegram_id not in settings.admin_ids:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={"message": "Administrator access required.", "code": "not_admin"},
        )
    return user
