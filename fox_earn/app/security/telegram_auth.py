from __future__ import annotations
import hashlib
import hmac
import json
import time
from typing import Any, Dict, Optional
from urllib.parse import parse_qsl, unquote

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from ..config import get_settings
from ..models import ReplayHash

settings = get_settings()


class TelegramAuthError(HTTPException):
    def __init__(self, detail: str, code: str = "invalid_init_data"):
        super().__init__(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"message": detail, "code": code},
        )


def _compute_secret_key(bot_token: str) -> bytes:
    return hmac.new(b"WebAppData", bot_token.encode("utf-8"), hashlib.sha256).digest()


def verify_init_data(init_data: str, db: Optional[Session] = None) -> Dict[str, Any]:
    if not init_data or "hash=" not in init_data:
        raise TelegramAuthError("Missing Telegram init data.", "missing_init_data")
    if not settings.bot_token:
        raise TelegramAuthError("Server is not configured with BOT_TOKEN.", "server_misconfigured")

    try:
        pairs = dict(parse_qsl(init_data, keep_blank_values=True))
    except Exception:
        raise TelegramAuthError("init data malformed.", "bad_init_data")

    provided_hash = pairs.pop("hash", "")
    if not provided_hash:
        raise TelegramAuthError("init data has no hash.", "missing_hash")

    data_check_string = "\n".join(k + "=" + v for k, v in sorted(pairs.items()))
    secret = _compute_secret_key(settings.bot_token)
    computed = hmac.new(secret, data_check_string.encode("utf-8"), hashlib.sha256).hexdigest()

    if not hmac.compare_digest(computed, provided_hash):
        raise TelegramAuthError("Telegram signature is invalid.", "bad_signature")

    try:
        auth_date = int(pairs.get("auth_date", "0"))
    except ValueError:
        raise TelegramAuthError("init data auth_date is not a number.", "bad_auth_date")

    age = time.time() - auth_date
    if age > settings.initdata_max_age_seconds:
        raise TelegramAuthError("Telegram login expired. Please reopen the Mini App.", "expired_init_data")

    if db is not None:
        hash_hex = hashlib.sha256(init_data.encode("utf-8")).hexdigest()
        exists = db.query(ReplayHash).filter(ReplayHash.hash_hex == hash_hex).first()
        if exists:
            raise TelegramAuthError("This login was already used. Reopen the app.", "replay_detected")
        db.add(ReplayHash(hash_hex=hash_hex))
        db.commit()

    user_raw = pairs.get("user")
    if not user_raw:
        raise TelegramAuthError("init data has no user.", "missing_user")
    try:
        user = json.loads(unquote(user_raw))
    except Exception:
        try:
            user = json.loads(user_raw)
        except Exception:
            raise TelegramAuthError("Could not parse user.", "bad_user_json")

    if not isinstance(user, dict) or "id" not in user:
        raise TelegramAuthError("init data user is malformed.", "bad_user")

    return {"user": user, "auth_date": auth_date, "hash": provided_hash}
