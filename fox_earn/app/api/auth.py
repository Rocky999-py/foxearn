from __future__ import annotations
import secrets
import time
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import User, SessionToken
from ..schemas import AuthIn, AuthOut
from ..security.telegram_auth import verify_init_data, TelegramAuthError
from ..services import referral_service
from ..config import get_settings
from ..settings_store import get_int

router = APIRouter()
settings = get_settings()


@router.post("/telegram", response_model=AuthOut)
def auth_telegram(payload: AuthIn, db: Session = Depends(get_db)):
    if get_int(db, "maintenance_mode", settings.maintenance_mode):
        raise HTTPException(status_code=503, detail={"message": "Maintenance mode.", "code": "maintenance_mode"})

    try:
        data = verify_init_data(payload.init_data, db=db)
    except TelegramAuthError:
        raise
    except Exception as exc:
        raise HTTPException(status_code=401, detail={"message": str(exc), "code": "auth_error"})

    u = data["user"]
    tg_id = int(u["id"])

    user = db.query(User).filter(User.telegram_id == tg_id).first()
    created = False
    if user is None:
        user = User(
            telegram_id=tg_id,
            username=u.get("username"),
            first_name=u.get("first_name"),
            last_name=u.get("last_name"),
            photo_url=u.get("photo_url"),
            language_code=u.get("language_code"),
            balance=0,
        )
        db.add(user); db.commit(); db.refresh(user); created = True

    user.username = u.get("username") or user.username
    user.first_name = u.get("first_name") or user.first_name
    user.last_name = u.get("last_name") or user.last_name
    user.photo_url = u.get("photo_url") or user.photo_url
    db.commit()

    if created:
        from urllib.parse import parse_qsl
        try:
            pairs = dict(parse_qsl(payload.init_data, keep_blank_values=True))
            sp = pairs.get("start_param", "")
            if sp.startswith("ref_"):
                try:
                    ref_tg = int(sp[4:])
                    referral_service.process_referral(db, user, ref_tg)
                except ValueError:
                    pass
        except Exception:
            pass

    token = secrets.token_urlsafe(32)
    expires = int(time.time()) + settings.session_ttl_seconds
    db.add(SessionToken(token=token, user_id=user.id, expires_at=expires))
    db.commit()

    is_admin = user.telegram_id in settings.admin_ids
    return AuthOut(
        token=token,
        user={
            "telegram_id": user.telegram_id,
            "display_name": user.display_name,
            "username": user.username,
            "photo_url": user.photo_url,
        },
        is_admin=is_admin,
    )
