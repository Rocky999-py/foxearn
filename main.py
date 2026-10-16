#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
FOX EARN - one-shot scaffolding script for PythonAnywhere deployment.
Creates a unified FastAPI project that serves frontend + API + admin panel.

Usage:
    python setup_fox_earn.py

After it finishes, follow the printed PythonAnywhere instructions.
"""
import os
import sys
import subprocess
from pathlib import Path

ROOT = Path("fox_earn").resolve()
IS_WIN = os.name == "nt"
VENV_DIR = ROOT / ".venv"
VENV_BIN = VENV_DIR / ("Scripts" if IS_WIN else "bin")
PY = VENV_BIN / ("python.exe" if IS_WIN else "python")

FILES = {}

# ============================================================================
# ROOT FILES
# ============================================================================
FILES[".gitignore"] = r'''__pycache__/
*.py[cod]
.venv/
venv/
.pytest_cache/
.env
*.db
*.sqlite
*.sqlite3
uploads/*
!uploads/.gitkeep
'''

FILES["requirements.txt"] = r'''fastapi==0.115.0
uvicorn[standard]==0.30.6
sqlalchemy==2.0.35
pydantic==2.9.2
pydantic-settings==2.5.2
python-dotenv==1.0.1
httpx==0.27.2
'''

FILES[".env.example"] = r'''BOT_TOKEN=REPLACE_WITH_YOUR_BOT_TOKEN
ADMIN_TELEGRAM_IDS=
BOT_USERNAME=foxxx_con_bot
FRONTEND_ORIGINS=http://127.0.0.1:8000,http://localhost:8000
SESSION_TTL_SECONDS=86400
INITDATA_MAX_AGE_SECONDS=3600
DATABASE_URL=sqlite:///./fox_earn.db
MAINTENANCE_MODE=0
DEBUG=0
'''

FILES["README.md"] = r'''# FOX EARN

Unified FastAPI app: serves frontend, admin panel, and API from one process.
Deployable to PythonAnywhere (or any ASGI host).

Local:
    python run.py

Cloud:
    See RUN_ON_PYTHONANYWHERE.md
'''

FILES["RUN_ON_PYTHONANYWHERE.md"] = r'''# Deploy on PythonAnywhere

## 1. Upload the project
Open a Bash console on PythonAnywhere and either:
    git clone YOUR_REPO_URL fox_earn
or use the Files tab to upload the fox_earn folder.

## 2. Create virtualenv and install packages
    cd ~/fox_earn
    mkvirtualenv --python=/usr/bin/python3.10 fox_earn_venv
    pip install -r requirements.txt

## 3. Initialize the database
    python scripts/init_db.py

## 4. Create the web app
Web tab -> Add a new web app -> Manual configuration -> Python 3.10

  Source code:       /home/YOUR_USERNAME/fox_earn
  Working directory: /home/YOUR_USERNAME/fox_earn
  Virtualenv:        /home/YOUR_USERNAME/.virtualenvs/fox_earn_venv

## 5. WSGI file
Click the WSGI configuration file link. Delete everything, paste:

    import sys
    path = "/home/YOUR_USERNAME/fox_earn"
    if path not in sys.path:
        sys.path.insert(0, path)
    from app.main import app as application

## 6. Environment variables
Web tab -> Environment variables. Add:

  BOT_TOKEN            = your bot token from @BotFather
  ADMIN_TELEGRAM_IDS   = your numeric Telegram ID
  BOT_USERNAME         = foxxx_con_bot
  FRONTEND_ORIGINS     = https://YOUR_USERNAME.pythonanywhere.com
  DATABASE_URL         = sqlite:////home/YOUR_USERNAME/fox_earn/fox_earn.db
  SESSION_TTL_SECONDS  = 86400
  INITDATA_MAX_AGE_SECONDS = 3600
  MAINTENANCE_MODE     = 0
  DEBUG                = 0

Note the FOUR slashes in DATABASE_URL: sqlite:////home/...

## 7. Enable HTTPS
Web tab -> Security -> Force HTTPS: On.
PythonAnywhere provisions a free Let's Encrypt certificate.

## 8. Reload
Click the green Reload button. Done.

## 9. Point BotFather at it
@BotFather -> /mybots -> your bot -> Bot Settings -> Menu Button
URL: https://YOUR_USERNAME.pythonanywhere.com

## Admin panel
https://YOUR_USERNAME.pythonanywhere.com/admin/

Only opens for Telegram IDs listed in ADMIN_TELEGRAM_IDS.

## Custom domain (optional)
Web tab -> Add a new domain, then set a CNAME from your DNS provider.
Enable a certificate for the custom domain in the same tab.
Update FRONTEND_ORIGINS env var and reload.
'''

FILES["run.py"] = r'''#!/usr/bin/env python3
"""Local launcher for FOX EARN."""
import os
import sys
import subprocess
from pathlib import Path

HERE = Path(__file__).resolve().parent
VENV_PY = HERE / ".venv" / ("Scripts" if os.name == "nt" else "bin") / ("python.exe" if os.name == "nt" else "python")

if not VENV_PY.exists():
    print("Creating virtual environment...")
    subprocess.check_call([sys.executable, "-m", "venv", str(HERE / ".venv")])

REQS = HERE / "requirements.txt"
MARKER = VENV_PY.parent / ".installed"

if not MARKER.exists() and REQS.exists():
    print("Installing requirements (one time)...")
    subprocess.check_call([str(VENV_PY), "-m", "pip", "install", "--upgrade", "pip"])
    subprocess.check_call([str(VENV_PY), "-m", "pip", "install", "-r", str(REQS)])
    MARKER.write_text("ok", encoding="utf-8")

ENV = HERE / ".env"
if not ENV.exists():
    ex = HERE / ".env.example"
    if ex.exists():
        ENV.write_text(ex.read_text(encoding="utf-8"), encoding="utf-8")
        print(">>> EDIT .env NOW: BOT_TOKEN, ADMIN_TELEGRAM_IDS <<<")

print()
print("Starting http://127.0.0.1:8000")
print("Ctrl+C to stop.\n")

try:
    subprocess.check_call([
        str(VENV_PY), "-m", "uvicorn", "app.main:app",
        "--reload", "--host", "127.0.0.1", "--port", "8000"
    ], cwd=str(HERE))
except KeyboardInterrupt:
    print("\nStopped.")
'''

# ============================================================================
# BACKEND
# ============================================================================
FILES["app/__init__.py"] = ""
FILES["app/security/__init__.py"] = ""
FILES["app/api/__init__.py"] = ""
FILES["app/services/__init__.py"] = ""

FILES["app/config.py"] = r'''from __future__ import annotations
from functools import lru_cache
from typing import List
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    bot_token: str = ""
    admin_telegram_ids: str = ""
    bot_username: str = "foxxx_con_bot"
    frontend_origins: str = "http://127.0.0.1:8000,http://localhost:8000"
    session_ttl_seconds: int = 86400
    initdata_max_age_seconds: int = 3600
    database_url: str = "sqlite:///./fox_earn.db"
    maintenance_mode: int = 0
    debug: int = 0

    @property
    def admin_ids(self) -> List[int]:
        out = []
        for chunk in self.admin_telegram_ids.split(","):
            chunk = chunk.strip()
            if chunk:
                try:
                    out.append(int(chunk))
                except ValueError:
                    pass
        return out

    @property
    def origins(self) -> List[str]:
        return [o.strip() for o in self.frontend_origins.split(",") if o.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()
'''

FILES["app/database.py"] = r'''from __future__ import annotations
from sqlalchemy import create_engine, event
from sqlalchemy.orm import declarative_base, sessionmaker
from .config import get_settings

settings = get_settings()

connect_args = {"check_same_thread": False} if settings.database_url.startswith("sqlite") else {}
engine = create_engine(
    settings.database_url,
    connect_args=connect_args,
    pool_pre_ping=True,
    echo=bool(settings.debug),
)

if settings.database_url.startswith("sqlite"):
    @event.listens_for(engine, "connect")
    def _set_sqlite_pragma(dbapi_connection, connection_record):
        try:
            cur = dbapi_connection.cursor()
            cur.execute("PRAGMA journal_mode=WAL;")
            cur.execute("PRAGMA foreign_keys=ON;")
            cur.close()
        except Exception:
            pass

SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, expire_on_commit=False)
Base = declarative_base()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db() -> None:
    from . import models  # noqa
    Base.metadata.create_all(bind=engine)
'''

FILES["app/models.py"] = r'''from __future__ import annotations
from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, DateTime, Boolean, BigInteger, Text, UniqueConstraint, Index
from .database import Base


def utcnow():
    return datetime.now(timezone.utc)


class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True)
    telegram_id = Column(BigInteger, unique=True, index=True, nullable=False)
    username = Column(String(128), nullable=True)
    first_name = Column(String(128), nullable=True)
    last_name = Column(String(128), nullable=True)
    photo_url = Column(String(512), nullable=True)
    language_code = Column(String(8), nullable=True)
    balance = Column(BigInteger, default=0, nullable=False)
    dollar_balance_cents = Column(BigInteger, default=0, nullable=False)
    locked_cents = Column(BigInteger, default=0, nullable=False)
    total_earned = Column(BigInteger, default=0, nullable=False)
    wallet_active = Column(Boolean, default=False, nullable=False)
    wallet_activated_at = Column(DateTime(timezone=True), nullable=True)
    referred_by_id = Column(Integer, nullable=True)
    is_banned = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime(timezone=True), default=utcnow, nullable=False)
    updated_at = Column(DateTime(timezone=True), default=utcnow, onupdate=utcnow, nullable=False)

    @property
    def display_name(self) -> str:
        name = " ".join(filter(None, [self.first_name, self.last_name])).strip()
        return name or (self.username and ("@" + self.username)) or ("Fox #" + str(self.id))

    @property
    def withdrawable_cents(self) -> int:
        return max(0, int(self.dollar_balance_cents or 0) - int(self.locked_cents or 0))


class SessionToken(Base):
    __tablename__ = "session_tokens"
    id = Column(Integer, primary_key=True)
    token = Column(String(64), unique=True, index=True, nullable=False)
    user_id = Column(Integer, index=True, nullable=False)
    expires_at = Column(BigInteger, nullable=False)
    created_at = Column(DateTime(timezone=True), default=utcnow, nullable=False)


class IdempotencyKey(Base):
    __tablename__ = "idempotency_keys"
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, index=True, nullable=False)
    key = Column(String(128), index=True, nullable=False)
    response_json = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), default=utcnow, nullable=False)
    __table_args__ = (UniqueConstraint("user_id", "key", name="uq_idem_user_key"),)


class ReplayHash(Base):
    __tablename__ = "replay_hashes"
    id = Column(Integer, primary_key=True)
    hash_hex = Column(String(128), unique=True, index=True, nullable=False)
    created_at = Column(DateTime(timezone=True), default=utcnow, nullable=False)


class Transaction(Base):
    __tablename__ = "transactions"
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, index=True, nullable=False)
    type = Column(String(32), nullable=False)
    label = Column(String(160), nullable=False)
    amount = Column(BigInteger, nullable=False)
    unit = Column(String(8), default="coins")
    status = Column(String(16), default="completed", nullable=False)
    ref = Column(String(64), nullable=True)
    created_at = Column(DateTime(timezone=True), default=utcnow, nullable=False, index=True)


class Referral(Base):
    __tablename__ = "referrals"
    id = Column(Integer, primary_key=True)
    referrer_id = Column(Integer, index=True, nullable=False)
    referred_id = Column(Integer, unique=True, nullable=False)
    status = Column(String(16), default="valid", nullable=False)
    created_at = Column(DateTime(timezone=True), default=utcnow, nullable=False)


class ReferralClaim(Base):
    __tablename__ = "referral_claims"
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, index=True, nullable=False)
    milestone = Column(Integer, nullable=False)
    reward_cents = Column(BigInteger, nullable=False)
    created_at = Column(DateTime(timezone=True), default=utcnow, nullable=False)
    __table_args__ = (UniqueConstraint("user_id", "milestone", name="uq_ref_claim"),)


class WalletActivationRequest(Base):
    __tablename__ = "wallet_activation_requests"
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, index=True, nullable=False)
    method = Column(String(16), nullable=False)
    fee_cents = Column(BigInteger, nullable=False)
    tx_ref = Column(String(128), nullable=True)
    screenshot_path = Column(String(512), nullable=True)
    status = Column(String(16), default="pending", nullable=False, index=True)
    admin_note = Column(Text, nullable=True)
    reviewed_by_telegram_id = Column(BigInteger, nullable=True)
    reviewed_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), default=utcnow, nullable=False, index=True)


class Withdrawal(Base):
    __tablename__ = "withdrawals"
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, index=True, nullable=False)
    amount_cents = Column(BigInteger, nullable=False)
    method = Column(String(32), nullable=False)
    destination = Column(String(256), nullable=False)
    status = Column(String(16), default="pending", nullable=False)
    note = Column(Text, nullable=True)
    refunded = Column(Boolean, default=False, nullable=False)
    paid_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), default=utcnow, nullable=False, index=True)
    updated_at = Column(DateTime(timezone=True), default=utcnow, onupdate=utcnow, nullable=False)


class Setting(Base):
    __tablename__ = "settings"
    key = Column(String(64), primary_key=True)
    value = Column(Text, nullable=False)


class AuditLog(Base):
    __tablename__ = "audit_logs"
    id = Column(Integer, primary_key=True)
    actor_telegram_id = Column(BigInteger, nullable=True)
    actor = Column(String(128), nullable=True)
    action = Column(String(64), nullable=False)
    details = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), default=utcnow, nullable=False, index=True)


Index("ix_tx_user_created", Transaction.user_id, Transaction.created_at.desc())
'''

FILES["app/schemas.py"] = r'''from __future__ import annotations
from typing import Optional
from pydantic import BaseModel, Field


class AuthIn(BaseModel):
    init_data: str = Field(min_length=10)


class AuthOut(BaseModel):
    token: str
    user: dict
    is_admin: bool


class TapIn(BaseModel):
    taps: int = Field(ge=1, le=1000)
    batch_id: str = Field(min_length=4, max_length=128)


class WithdrawalIn(BaseModel):
    amount_cents: int = Field(gt=0)
    method: str = Field(min_length=1, max_length=32)
    destination: str = Field(min_length=1, max_length=256)
    idempotency_key: Optional[str] = None


class WalletActivationSubmitIn(BaseModel):
    method: str = Field(min_length=1, max_length=16)
    tx_ref: Optional[str] = ""
    screenshot_base64: str = Field(min_length=20)


class ReferralClaimIn(BaseModel):
    milestone: int = Field(ge=1, le=100)


class AdminWithdrawalAction(BaseModel):
    action: str
    note: Optional[str] = ""


class AdminWalletActivationAction(BaseModel):
    action: str
    note: Optional[str] = ""


class AdminSettingsPatch(BaseModel):
    updates: dict


class AdminTimerIn(BaseModel):
    target_local: str = ""
    enabled: bool = False
'''

FILES["app/settings_store.py"] = r'''from __future__ import annotations
from typing import Any, Dict
from sqlalchemy.orm import Session
from .models import Setting

DEFAULTS: Dict[str, str] = {
    "coins_per_tap": "1",
    "referral_min_valid": "3",
    "referral_milestones_count": "10",
    "referral_reward_cents": "1000",
    "wallet_activation_enabled": "0",
    "wallet_activation_fee_cents": "2000",
    "wallet_method_okx_enabled": "1",
    "wallet_method_bybit_enabled": "1",
    "wallet_method_binance_enabled": "1",
    "wallet_instr_okx": "Send $20 USDT to the OKX account configured by admin, then upload a screenshot.",
    "wallet_instr_bybit": "Send $20 USDT to the Bybit account configured by admin, then upload a screenshot.",
    "wallet_instr_binance": "Send $20 via Binance Pay ID configured by admin, then upload a screenshot.",
    "wallet_dest_okx": "",
    "wallet_dest_bybit": "",
    "wallet_dest_binance": "",
    "screenshot_max_mb": "5",
    "withdrawal_enabled": "1",
    "min_withdrawal_cents": "500",
    "max_withdrawal_cents": "0",
    "withdrawal_methods": "binance: Binance Pay, okx: OKX, bybit: Bybit",
    "withdrawal_timer_enabled": "0",
    "withdrawal_target_local": "",
    "withdrawal_target_utc_ms": "0",
    "maintenance_mode": "0",
    "coins_per_usd": "5000",
}


def get_setting(db: Session, key: str) -> str:
    row = db.get(Setting, key)
    if row is None:
        return DEFAULTS.get(key, "")
    return row.value


def set_setting(db: Session, key: str, value: Any) -> None:
    row = db.get(Setting, key)
    if row is None:
        db.add(Setting(key=key, value=str(value)))
    else:
        row.value = str(value)
    db.commit()


def get_int(db: Session, key: str, default: int = 0) -> int:
    try:
        return int(get_setting(db, key))
    except (TypeError, ValueError):
        return default


def ensure_defaults(db: Session) -> None:
    for k, v in DEFAULTS.items():
        if db.get(Setting, k) is None:
            db.add(Setting(key=k, value=v))
    db.commit()
'''

FILES["app/ratelimit.py"] = r'''from __future__ import annotations
import time
from collections import defaultdict, deque
from threading import Lock
from typing import Deque, Dict, Tuple

_LOCK = Lock()
_BUCKETS: Dict[Tuple[str, str], Deque[float]] = defaultdict(deque)


def allow(key: str, subject: str, max_events: int, window_seconds: float) -> bool:
    now = time.monotonic()
    cutoff = now - window_seconds
    with _LOCK:
        bucket = _BUCKETS[(key, subject)]
        while bucket and bucket[0] < cutoff:
            bucket.popleft()
        if len(bucket) >= max_events:
            return False
        bucket.append(now)
        return True
'''

FILES["app/deps.py"] = r'''from __future__ import annotations
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
'''

FILES["app/security/telegram_auth.py"] = r'''from __future__ import annotations
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
'''

FILES["app/security/permissions.py"] = r'''from __future__ import annotations
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
'''

FILES["app/services/audit_service.py"] = r'''from __future__ import annotations
import json
from typing import Any, Optional
from sqlalchemy.orm import Session
from ..models import AuditLog


def log(db: Session, action: str, actor: Optional[str] = None, actor_telegram_id: Optional[int] = None, details: Any = None) -> None:
    entry = AuditLog(
        actor=actor,
        actor_telegram_id=actor_telegram_id,
        action=action,
        details=json.dumps(details, default=str)[:4000] if details else None,
    )
    db.add(entry)
    db.commit()
'''

FILES["app/services/earning_service.py"] = r'''from __future__ import annotations
from sqlalchemy.orm import Session
from ..models import User, Transaction
from ..settings_store import get_int


def process_taps(db: Session, user: User, taps: int) -> dict:
    coins_per_tap = max(1, get_int(db, "coins_per_tap", 1))
    reward = taps * coins_per_tap

    user.balance = (user.balance or 0) + reward
    user.total_earned = (user.total_earned or 0) + reward

    db.add(Transaction(
        user_id=user.id, type="tap_reward",
        label="Tap reward (" + str(taps) + ")",
        amount=reward, unit="coins", status="completed",
    ))
    db.commit()
    db.refresh(user)

    return {
        "accepted": taps,
        "balance": int(user.balance or 0),
        "dollar_balance_cents": int(user.dollar_balance_cents or 0),
        "total_earned": int(user.total_earned or 0),
    }
'''

FILES["app/services/referral_service.py"] = r'''from __future__ import annotations
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
'''

FILES["app/services/wallet_activation_service.py"] = r'''from __future__ import annotations
from datetime import datetime, timezone
from sqlalchemy.orm import Session
from ..models import User, WalletActivationRequest
from ..settings_store import get_int, get_setting


def methods_configured(db: Session) -> list:
    out = []
    for code, label in (("okx", "OKX"), ("bybit", "Bybit"), ("binance", "Binance")):
        if get_int(db, "wallet_method_" + code + "_enabled", 1):
            out.append({
                "code": code,
                "label": label,
                "fee_cents": get_int(db, "wallet_activation_fee_cents", 2000),
                "instructions": get_setting(db, "wallet_instr_" + code),
                "destination": get_setting(db, "wallet_dest_" + code),
            })
    return out


def create_request(db: Session, user: User, method: str, screenshot_path, tx_ref: str) -> WalletActivationRequest:
    fee = get_int(db, "wallet_activation_fee_cents", 2000)
    req = WalletActivationRequest(
        user_id=user.id, method=method, fee_cents=fee,
        tx_ref=tx_ref[:128] if tx_ref else None,
        screenshot_path=screenshot_path, status="pending",
    )
    db.add(req); db.commit(); db.refresh(req)
    return req


def admin_action(db: Session, req_id: int, action: str, admin_telegram_id: int, note: str = "") -> dict:
    req = db.get(WalletActivationRequest, req_id)
    if req is None:
        return {"ok": False, "message": "Request not found."}
    user = db.get(User, req.user_id)
    if user is None:
        return {"ok": False, "message": "User not found."}

    action = action.lower().strip()

    if action == "approve":
        if req.status == "approved":
            return {"ok": False, "message": "Already approved."}
        req.status = "approved"
        req.admin_note = (note or "")[:2000]
        req.reviewed_by_telegram_id = admin_telegram_id
        req.reviewed_at = datetime.now(timezone.utc)
        user.wallet_active = True
        user.wallet_activated_at = datetime.now(timezone.utc)
        db.commit()
        return {"ok": True, "status": req.status}

    if action == "reject":
        if req.status == "rejected":
            return {"ok": False, "message": "Already rejected."}
        req.status = "rejected"
        req.admin_note = (note or "Rejected")[:2000]
        req.reviewed_by_telegram_id = admin_telegram_id
        req.reviewed_at = datetime.now(timezone.utc)
        db.commit()
        return {"ok": True, "status": req.status}

    return {"ok": False, "message": "Unknown action " + action + "."}
'''

FILES["app/services/withdrawal_service.py"] = r'''from __future__ import annotations
from datetime import datetime, timezone
from sqlalchemy.orm import Session
from ..models import User, Withdrawal, Transaction
from ..settings_store import get_int


def withdrawal_window_open(db: Session) -> bool:
    if not get_int(db, "withdrawal_enabled", 1):
        return False
    if not get_int(db, "withdrawal_timer_enabled", 0):
        return True
    target_ms = get_int(db, "withdrawal_target_utc_ms", 0)
    if target_ms <= 0:
        return True
    return int(datetime.now(timezone.utc).timestamp() * 1000) >= target_ms


def create_withdrawal(db: Session, user: User, amount_cents: int, method: str, destination: str) -> dict:
    if not get_int(db, "withdrawal_enabled", 1):
        return {"ok": False, "code": "disabled", "message": "Withdrawals are disabled."}
    if not user.wallet_active:
        return {"ok": False, "code": "no_wallet", "message": "Activate your wallet first."}
    if not withdrawal_window_open(db):
        return {"ok": False, "code": "window_closed", "message": "Withdrawal window is closed."}

    min_c = get_int(db, "min_withdrawal_cents", 500)
    max_c = get_int(db, "max_withdrawal_cents", 0)
    if amount_cents < min_c:
        return {"ok": False, "code": "below_min", "message": "Minimum withdrawal is $" + format(min_c/100, ".2f") + "."}
    if max_c and amount_cents > max_c:
        return {"ok": False, "code": "above_max", "message": "Maximum withdrawal is $" + format(max_c/100, ".2f") + "."}
    if amount_cents > user.withdrawable_cents:
        return {"ok": False, "code": "insufficient", "message": "Not enough withdrawable balance."}

    user.locked_cents = (user.locked_cents or 0) + amount_cents
    wd = Withdrawal(user_id=user.id, amount_cents=amount_cents, method=method, destination=destination, status="pending")
    db.add(wd)
    db.add(Transaction(user_id=user.id, type="withdrawal_reserve",
                       label="Reserved for withdrawal", amount=-amount_cents,
                       unit="usd_cents", status="pending"))
    db.commit(); db.refresh(wd)
    return {"ok": True, "id": wd.id, "status": wd.status}


def apply_admin_action(db: Session, wd_id: int, action: str, note: str = "") -> dict:
    wd = db.get(Withdrawal, wd_id)
    if wd is None:
        return {"ok": False, "message": "Not found."}
    user = db.get(User, wd.user_id)
    if user is None:
        return {"ok": False, "message": "User not found."}

    action = action.lower().strip()
    if action == "approve":
        if wd.status != "pending":
            return {"ok": False, "message": "Cannot approve a " + wd.status + " withdrawal."}
        wd.status = "approved"; wd.note = note
        db.commit()
        return {"ok": True, "status": wd.status}

    if action == "reject":
        if wd.status not in ("pending", "approved"):
            return {"ok": False, "message": "Cannot reject a " + wd.status + " withdrawal."}
        if wd.refunded:
            return {"ok": False, "message": "Already refunded."}
        user.locked_cents = max(0, (user.locked_cents or 0) - wd.amount_cents)
        wd.refunded = True; wd.status = "rejected"; wd.note = note
        db.add(Transaction(user_id=user.id, type="withdrawal_refund",
                           label="Refund for withdrawal #" + str(wd.id), amount=wd.amount_cents,
                           unit="usd_cents", status="completed"))
        db.commit()
        return {"ok": True, "status": wd.status}

    if action == "paid":
        if wd.status != "approved":
            return {"ok": False, "message": "Approve first."}
        user.locked_cents = max(0, (user.locked_cents or 0) - wd.amount_cents)
        user.dollar_balance_cents = max(0, (user.dollar_balance_cents or 0) - wd.amount_cents)
        wd.status = "paid"; wd.paid_at = datetime.now(timezone.utc); wd.note = note
        db.add(Transaction(user_id=user.id, type="withdrawal_paid",
                           label="Withdrawal #" + str(wd.id) + " paid", amount=0,
                           unit="usd_cents", status="completed"))
        db.commit()
        return {"ok": True, "status": wd.status}

    return {"ok": False, "message": "Unknown action " + action + "."}
'''

# ============================================================================
# API ROUTERS
# ============================================================================
FILES["app/api/auth.py"] = r'''from __future__ import annotations
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
'''

FILES["app/api/users.py"] = r'''from __future__ import annotations
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
'''

FILES["app/api/taps.py"] = r'''from __future__ import annotations
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
'''

FILES["app/api/referrals.py"] = r'''from __future__ import annotations
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
'''

FILES["app/api/transactions.py"] = r'''from __future__ import annotations
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
'''

FILES["app/api/leaderboard.py"] = r'''from __future__ import annotations
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
'''

FILES["app/api/tasks.py"] = r'''from __future__ import annotations
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from ..database import get_db
from ..deps import get_current_user
from ..models import User

router = APIRouter()


@router.get("/tasks")
def list_tasks(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return {"tasks": []}
'''

FILES["app/api/wallet.py"] = r'''from __future__ import annotations
import base64
import binascii
import json
import re
import secrets
import time
from pathlib import Path
from fastapi import APIRouter, Depends, HTTPException, Response
from sqlalchemy.orm import Session

from ..database import get_db
from ..deps import get_current_user
from ..models import User, Withdrawal, WalletActivationRequest, IdempotencyKey
from ..schemas import WithdrawalIn, WalletActivationSubmitIn
from ..services import withdrawal_service, wallet_activation_service
from ..settings_store import get_int, get_setting
from ..config import get_settings

router = APIRouter()
settings = get_settings()

UPLOAD_ROOT = Path(__file__).resolve().parents[2] / "uploads"
WALLET_DIR = UPLOAD_ROOT / "wallet"
WALLET_DIR.mkdir(parents=True, exist_ok=True)


def _detect_image_type(raw: bytes):
    if raw.startswith(b"\x89PNG\r\n\x1a\n"):
        return "image/png"
    if raw.startswith(b"\xff\xd8\xff"):
        return "image/jpeg"
    if len(raw) >= 12 and raw[0:4] == b"RIFF" and raw[8:12] == b"WEBP":
        return "image/webp"
    return None


def _save(data_url: str, user_id: int, max_mb: int) -> str:
    m = re.match(r"^data:([^;]+);base64,(.+)$", data_url)
    if m:
        mime, b64 = m.group(1).lower(), m.group(2)
    else:
        mime, b64 = "image/png", data_url
    if mime not in ("image/png", "image/jpeg", "image/jpg", "image/webp"):
        raise ValueError("Unsupported image type.")
    try:
        raw = base64.b64decode(b64, validate=True)
    except (binascii.Error, ValueError):
        raise ValueError("Invalid base64.")
    if len(raw) > max_mb * 1024 * 1024:
        raise ValueError("Image exceeds " + str(max_mb) + " MB.")
    detected = _detect_image_type(raw)
    if not detected:
        raise ValueError("File does not look like PNG/JPG/WEBP.")
    ext = {"image/png": "png", "image/jpeg": "jpg", "image/webp": "webp"}[detected]
    fn = "wa_" + str(user_id) + "_" + str(int(time.time())) + "_" + secrets.token_hex(6) + "." + ext
    with open(WALLET_DIR / fn, "wb") as f:
        f.write(raw)
    return fn


def _parse_methods(raw: str):
    out = []
    for chunk in raw.split(","):
        chunk = chunk.strip()
        if not chunk or ":" not in chunk:
            continue
        c, l = chunk.split(":", 1)
        out.append({"code": c.strip(), "label": l.strip()})
    return out


@router.get("/wallet")
def get_wallet(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    wallet_enabled = bool(get_int(db, "wallet_activation_enabled", 0))
    fee_cents = get_int(db, "wallet_activation_fee_cents", 2000)
    withdrawal_methods = _parse_methods(get_setting(db, "withdrawal_methods"))

    activations = db.query(WalletActivationRequest)\
        .filter(WalletActivationRequest.user_id == user.id)\
        .order_by(WalletActivationRequest.created_at.desc()).limit(20).all()

    withdrawals = db.query(Withdrawal)\
        .filter(Withdrawal.user_id == user.id)\
        .order_by(Withdrawal.created_at.desc()).limit(20).all()

    timer_enabled = bool(get_int(db, "withdrawal_timer_enabled", 0))
    target_ms = get_int(db, "withdrawal_target_utc_ms", 0)
    open_now = withdrawal_service.withdrawal_window_open(db)

    return {
        "summary": {
            "balance": int(user.balance or 0),
            "dollar_balance_cents": int(user.dollar_balance_cents or 0),
            "withdrawable_cents": int(user.withdrawable_cents),
            "locked_cents": int(user.locked_cents or 0),
        },
        "wallet_active": bool(user.wallet_active),
        "wallet_enabled": wallet_enabled,
        "wallet_fee_cents": fee_cents,
        "wallet_methods": wallet_activation_service.methods_configured(db) if wallet_enabled else [],
        "wallet_activations": [
            {
                "id": a.id, "method": a.method, "fee_cents": a.fee_cents,
                "status": a.status, "admin_note": a.admin_note,
                "has_screenshot": bool(a.screenshot_path),
                "created_at": a.created_at.isoformat() if a.created_at else None,
            } for a in activations
        ],
        "min_withdrawal_cents": get_int(db, "min_withdrawal_cents", 500),
        "max_withdrawal_cents": get_int(db, "max_withdrawal_cents", 0),
        "withdrawal_methods": withdrawal_methods,
        "withdrawals": [
            {
                "id": w.id, "amount_cents": w.amount_cents, "method": w.method,
                "status": w.status,
                "created_at": w.created_at.isoformat() if w.created_at else None,
            } for w in withdrawals
        ],
        "withdrawal_timer_enabled": timer_enabled,
        "withdrawal_target_ms": target_ms,
        "withdrawal_open": open_now,
    }


@router.post("/wallet/activate/submit")
def wallet_activate_submit(payload: WalletActivationSubmitIn, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    if not get_int(db, "wallet_activation_enabled", 0):
        raise HTTPException(status_code=400, detail={"message": "Add Wallet is locked.", "code": "locked"})
    if payload.method not in ("okx", "bybit", "binance"):
        raise HTTPException(status_code=400, detail={"message": "Unknown method.", "code": "bad_method"})
    if not get_int(db, "wallet_method_" + payload.method + "_enabled", 1):
        raise HTTPException(status_code=400, detail={"message": "Method disabled.", "code": "method_disabled"})

    max_mb = max(1, get_int(db, "screenshot_max_mb", 5))
    try:
        filename = _save(payload.screenshot_base64, user.id, max_mb)
    except ValueError as e:
        raise HTTPException(status_code=400, detail={"message": str(e), "code": "bad_screenshot"})

    req = wallet_activation_service.create_request(db, user, payload.method, filename, payload.tx_ref or "")
    return {"id": req.id, "status": req.status}


@router.get("/wallet/activate/{req_id}/screenshot")
def wallet_activation_screenshot(req_id: int, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    req = db.get(WalletActivationRequest, req_id)
    if req is None:
        raise HTTPException(status_code=404, detail={"message": "Not found.", "code": "not_found"})
    is_admin = user.telegram_id in settings.admin_ids
    if req.user_id != user.id and not is_admin:
        raise HTTPException(status_code=403, detail={"message": "Forbidden.", "code": "forbidden"})
    if not req.screenshot_path:
        raise HTTPException(status_code=404, detail={"message": "No screenshot.", "code": "no_screenshot"})
    path = WALLET_DIR / req.screenshot_path
    if not path.exists():
        raise HTTPException(status_code=404, detail={"message": "Missing file.", "code": "file_missing"})
    ext = path.suffix.lower()
    mime = "image/png" if ext == ".png" else "image/webp" if ext == ".webp" else "image/jpeg"
    return Response(content=path.read_bytes(), media_type=mime, headers={"Cache-Control": "private, max-age=60"})


@router.post("/withdrawals")
def create_withdrawal(payload: WithdrawalIn, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    if payload.idempotency_key:
        existing = db.query(IdempotencyKey).filter(
            IdempotencyKey.user_id == user.id, IdempotencyKey.key == payload.idempotency_key
        ).first()
        if existing:
            try:
                return json.loads(existing.response_json or "{}")
            except Exception:
                pass

    result = withdrawal_service.create_withdrawal(db, user, payload.amount_cents, payload.method, payload.destination)
    if not result.get("ok"):
        raise HTTPException(status_code=400, detail={"message": result["message"], "code": result.get("code", "withdrawal_error")})

    response = {"id": result["id"], "status": result["status"]}
    if payload.idempotency_key:
        db.add(IdempotencyKey(user_id=user.id, key=payload.idempotency_key, response_json=json.dumps(response)))
        db.commit()
    return response
'''

FILES["app/api/admin.py"] = r'''from __future__ import annotations
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func
from sqlalchemy.orm import Session

from ..database import get_db
from ..deps import get_current_user
from ..models import User, Withdrawal, WalletActivationRequest, Task, Setting, AuditLog
from ..schemas import AdminWithdrawalAction, AdminWalletActivationAction, AdminSettingsPatch, AdminTimerIn
from ..security.permissions import require_admin
from ..services import withdrawal_service, wallet_activation_service, audit_service
from ..settings_store import set_setting

router = APIRouter()


@router.get("/admin/overview")
def overview(admin: User = Depends(require_admin), db: Session = Depends(get_db)):
    total_users = db.query(func.count(User.id)).scalar() or 0
    total_coins = db.query(func.coalesce(func.sum(User.balance), 0)).scalar() or 0
    total_usd = db.query(func.coalesce(func.sum(User.dollar_balance_cents), 0)).scalar() or 0
    pending_w = db.query(func.count(Withdrawal.id)).filter(Withdrawal.status == "pending").scalar() or 0
    pending_a = db.query(func.count(WalletActivationRequest.id)).filter(WalletActivationRequest.status == "pending").scalar() or 0
    return {"stats": {
        "total_users": int(total_users),
        "total_coins": int(total_coins),
        "total_dollar_cents": int(total_usd),
        "pending_wallet_activations": int(pending_a),
        "pending_withdrawals": int(pending_w),
    }}


@router.get("/admin/wallet-activations")
def list_activations(status: str = Query(default="pending"), limit: int = Query(default=50, ge=1, le=200),
                     admin: User = Depends(require_admin), db: Session = Depends(get_db)):
    q = db.query(WalletActivationRequest)
    if status:
        q = q.filter(WalletActivationRequest.status == status)
    rows = q.order_by(WalletActivationRequest.created_at.desc()).limit(limit).all()
    out = []
    for a in rows:
        u = db.get(User, a.user_id)
        out.append({
            "id": a.id, "method": a.method, "fee_cents": a.fee_cents,
            "tx_ref": a.tx_ref, "status": a.status, "admin_note": a.admin_note,
            "display_name": u.display_name if u else "User",
            "has_screenshot": bool(a.screenshot_path),
            "created_at": a.created_at.isoformat() if a.created_at else None,
        })
    return {"activations": out}


@router.post("/admin/wallet-activations/{rid}/action")
def activation_action(rid: int, payload: AdminWalletActivationAction,
                     admin: User = Depends(require_admin), db: Session = Depends(get_db)):
    result = wallet_activation_service.admin_action(db, rid, payload.action, admin.telegram_id, payload.note or "")
    if not result.get("ok"):
        raise HTTPException(status_code=400, detail={"message": result["message"], "code": "activation_failed"})
    audit_service.log(db, "wallet_activation_" + payload.action,
                      actor=admin.display_name, actor_telegram_id=admin.telegram_id,
                      details={"id": rid, "note": payload.note})
    return result


@router.get("/admin/withdrawals")
def list_withdrawals(status: str = Query(default="pending"), limit: int = Query(default=50, ge=1, le=200),
                     admin: User = Depends(require_admin), db: Session = Depends(get_db)):
    q = db.query(Withdrawal)
    if status:
        q = q.filter(Withdrawal.status == status)
    rows = q.order_by(Withdrawal.created_at.desc()).limit(limit).all()
    out = []
    for w in rows:
        u = db.get(User, w.user_id)
        out.append({
            "id": w.id, "amount_cents": w.amount_cents, "method": w.method,
            "destination": w.destination, "status": w.status,
            "display_name": u.display_name if u else "User",
            "created_at": w.created_at.isoformat() if w.created_at else None,
        })
    return {"withdrawals": out}


@router.post("/admin/withdrawals/{wid}/action")
def withdrawal_action(wid: int, payload: AdminWithdrawalAction,
                      admin: User = Depends(require_admin), db: Session = Depends(get_db)):
    result = withdrawal_service.apply_admin_action(db, wid, payload.action, payload.note or "")
    if not result.get("ok"):
        raise HTTPException(status_code=400, detail={"message": result["message"], "code": "withdrawal_failed"})
    audit_service.log(db, "withdrawal_" + payload.action,
                      actor=admin.display_name, actor_telegram_id=admin.telegram_id,
                      details={"id": wid, "note": payload.note})
    return result


@router.post("/admin/withdrawal-timer")
def set_withdrawal_timer(payload: AdminTimerIn, admin: User = Depends(require_admin), db: Session = Depends(get_db)):
    target_ms = 0
    if payload.target_local:
        try:
            dt_local = datetime.fromisoformat(payload.target_local)
            if dt_local.tzinfo is None:
                dt_local = dt_local.replace(tzinfo=timezone.utc)
            target_ms = int(dt_local.timestamp() * 1000)
        except Exception:
            raise HTTPException(status_code=400, detail={"message": "Invalid datetime.", "code": "bad_datetime"})
    set_setting(db, "withdrawal_timer_enabled", "1" if payload.enabled else "0")
    set_setting(db, "withdrawal_target_local", payload.target_local or "")
    set_setting(db, "withdrawal_target_utc_ms", str(target_ms))
    audit_service.log(db, "withdrawal_timer_set", actor=admin.display_name,
                      actor_telegram_id=admin.telegram_id,
                      details={"target": payload.target_local, "enabled": payload.enabled})
    return {"ok": True, "target_ms": target_ms, "enabled": payload.enabled}


@router.post("/admin/settings")
def patch_settings(payload: AdminSettingsPatch, admin: User = Depends(require_admin), db: Session = Depends(get_db)):
    allowed = {
        "wallet_activation_enabled", "wallet_activation_fee_cents",
        "wallet_method_okx_enabled", "wallet_method_bybit_enabled", "wallet_method_binance_enabled",
        "wallet_instr_okx", "wallet_instr_bybit", "wallet_instr_binance",
        "wallet_dest_okx", "wallet_dest_bybit", "wallet_dest_binance",
        "referral_min_valid", "referral_milestones_count", "referral_reward_cents",
        "withdrawal_enabled", "min_withdrawal_cents", "max_withdrawal_cents",
        "withdrawal_methods", "screenshot_max_mb", "maintenance_mode",
    }
    changed = {}
    for k, v in (payload.updates or {}).items():
        if k not in allowed:
            continue
        set_setting(db, k, str(v))
        changed[k] = str(v)
    audit_service.log(db, "settings_patch", actor=admin.display_name,
                      actor_telegram_id=admin.telegram_id, details=changed)
    return {"ok": True, "updated": list(changed.keys())}


@router.get("/admin/tasks")
def list_tasks(admin: User = Depends(require_admin), db: Session = Depends(get_db)):
    return {"tasks": []}


@router.get("/admin/settings")
def list_settings(admin: User = Depends(require_admin), db: Session = Depends(get_db)):
    rows = db.query(Setting).order_by(Setting.key.asc()).all()
    return {"settings": [{"key": r.key, "value": r.value} for r in rows]}


@router.get("/admin/audit")
def list_audit(limit: int = Query(default=50, ge=1, le=200),
               admin: User = Depends(require_admin), db: Session = Depends(get_db)):
    rows = db.query(AuditLog).order_by(AuditLog.created_at.desc()).limit(limit).all()
    return {"logs": [{"id": r.id, "action": r.action, "actor": r.actor or "system",
                      "created_at": r.created_at.isoformat() if r.created_at else None} for r in rows]}
'''

# ============================================================================
# MAIN APP (serves frontend + API)
# ============================================================================
FILES["app/main.py"] = r'''from __future__ import annotations
import logging
from pathlib import Path
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from starlette.middleware.base import BaseHTTPMiddleware

from .config import get_settings
from .database import init_db, SessionLocal
from .settings_store import ensure_defaults, get_int
from .api import auth, users, taps, tasks, referrals, wallet, transactions, leaderboard, admin as admin_api

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("fox_earn")
settings = get_settings()

app = FastAPI(title="FOX EARN API", version="3.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.origins,
    allow_credentials=False,
    allow_methods=["GET", "POST", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["*"],
    expose_headers=["*"],
)


class MaintenanceMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        path = request.url.path
        if (path.startswith("/health") or path.startswith("/api/auth")
            or path == "/" or path.startswith("/docs") or path.startswith("/openapi")
            or path.startswith("/assets") or path.startswith("/admin")):
            return await call_next(request)
        db = SessionLocal()
        try:
            if get_int(db, "maintenance_mode", settings.maintenance_mode):
                return JSONResponse(status_code=503, content={"detail": {"message": "Maintenance mode.", "code": "maintenance_mode"}})
        finally:
            db.close()
        return await call_next(request)


app.add_middleware(MaintenanceMiddleware)


@app.on_event("startup")
def startup():
    init_db()
    db = SessionLocal()
    try:
        ensure_defaults(db)
    finally:
        db.close()
    log.info("FOX EARN backend ready. CORS origins: %s", settings.origins)


@app.get("/health")
def health():
    return {"status": "ok", "app": "FOX EARN", "version": "3.0.0"}


# --- API routes (before static mount) ---
app.include_router(auth.router, prefix="/api/auth", tags=["auth"])
app.include_router(users.router, prefix="/api", tags=["users"])
app.include_router(taps.router, prefix="/api", tags=["taps"])
app.include_router(tasks.router, prefix="/api", tags=["tasks"])
app.include_router(referrals.router, prefix="/api", tags=["referrals"])
app.include_router(wallet.router, prefix="/api", tags=["wallet"])
app.include_router(transactions.router, prefix="/api", tags=["transactions"])
app.include_router(leaderboard.router, prefix="/api", tags=["leaderboard"])
app.include_router(admin_api.router, prefix="/api", tags=["admin"])


# --- Static frontend (mounted LAST) ---
FRONTEND_DIR = Path(__file__).resolve().parents[1] / "frontend"

if FRONTEND_DIR.exists():
    @app.get("/")
    def serve_index():
        return FileResponse(FRONTEND_DIR / "index.html")

    @app.get("/admin/")
    def serve_admin():
        return FileResponse(FRONTEND_DIR / "admin" / "index.html")

    app.mount("/assets", StaticFiles(directory=str(FRONTEND_DIR / "assets")), name="frontend-assets")
    log.info("Serving static frontend from %s", FRONTEND_DIR)
else:
    log.warning("Frontend folder not found at %s", FRONTEND_DIR)
'''

FILES["scripts/init_db.py"] = r'''#!/usr/bin/env python3
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
sys.path.insert(0, str(ROOT))

from app.database import init_db, SessionLocal  # noqa
from app.settings_store import ensure_defaults  # noqa


def main():
    init_db()
    db = SessionLocal()
    try:
        ensure_defaults(db)
    finally:
        db.close()
    print("Database initialized successfully.")


if __name__ == "__main__":
    main()
'''

# ============================================================================
# FRONTEND
# ============================================================================
FILES["frontend/index.html"] = r'''<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8"/>
<meta name="viewport" content="width=device-width,initial-scale=1,maximum-scale=1,user-scalable=no,viewport-fit=cover"/>
<meta name="theme-color" content="#070d1b"/>
<title>FOX EARN</title>
<link rel="preconnect" href="https://fonts.googleapis.com"/>
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin/>
<link href="https://fonts.googleapis.com/css2?family=Manrope:wght@400;500;600;700;800&display=swap" rel="stylesheet"/>
<link rel="stylesheet" href="/assets/css/style.css"/>
<script src="https://telegram.org/js/telegram-web-app.js"></script>
</head>
<body>
<div id="status-banner" class="status-banner" hidden><span id="status-banner-text"></span></div>
<div id="app" class="app">
<header class="app-header">
  <button id="back-btn" class="icon-btn" type="button" aria-label="Back" hidden>
    <svg viewBox="0 0 24 24"><path d="M15 18l-6-6 6-6" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/></svg>
  </button>
  <div class="brand">
    <svg class="brand-fox" viewBox="0 0 200 200" aria-hidden="true">
      <polygon points="40,72 28,14 86,50" fill="#ff8a3d"/>
      <polygon points="160,72 172,14 114,50" fill="#ff8a3d"/>
      <path d="M100 40 L166 76 L150 136 L100 172 L50 136 L34 76 Z" fill="#ff8a3d"/>
      <path d="M100 106 L136 131 L100 168 L64 131 Z" fill="#fff3e6"/>
      <circle cx="72" cy="101" r="8.5" fill="#0b1220"/>
      <circle cx="128" cy="101" r="8.5" fill="#0b1220"/>
    </svg>
    <span class="brand-name">FOX<span class="brand-name-accent">EARN</span></span>
  </div>
  <button id="refresh-btn" class="icon-btn" type="button" aria-label="Refresh">
    <svg viewBox="0 0 24 24"><path d="M21 12a9 9 0 1 1-2.64-6.36M21 3v6h-6" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/></svg>
  </button>
</header>

<main id="view" class="view">
<section class="screen" id="screen-home" data-screen="home">
  <div class="card profile-card">
    <div class="avatar" id="home-avatar"><span id="home-avatar-fallback">•</span></div>
    <div class="profile-meta">
      <p class="profile-hello">Welcome back,</p>
      <p class="profile-name" id="home-name">—</p>
      <p class="profile-sub" id="home-username">—</p>
    </div>
  </div>
  <div class="dual-balance">
    <div class="card balance-card">
      <p class="balance-label">Coin balance</p>
      <p class="balance-value"><span id="home-coins">0</span><span class="coin-dot"></span></p>
      <p class="balance-sub">Earn 1 coin per tap</p>
    </div>
    <div class="card balance-card dollar-card">
      <p class="balance-label">Dollar balance</p>
      <p class="balance-value dollar-value"><span id="home-dollars">$0.00</span></p>
      <p class="balance-sub">5,000 coins = $1</p>
    </div>
  </div>
  <div class="tap-zone">
    <button id="tap-button" class="tap-button" type="button" aria-label="Tap to earn">
      <span class="tap-ring"></span>
      <svg class="tap-fox" viewBox="0 0 200 200" aria-hidden="true">
        <polygon points="40,72 28,14 86,50" fill="#ff8a3d"/><polygon points="160,72 172,14 114,50" fill="#ff8a3d"/>
        <path d="M100 40 L166 76 L150 136 L100 172 L50 136 L34 76 Z" fill="#ff8a3d"/>
        <path d="M100 106 L136 131 L100 168 L64 131 Z" fill="#fff3e6"/>
        <circle cx="72" cy="101" r="8.5" fill="#0b1220"/><circle cx="128" cy="101" r="8.5" fill="#0b1220"/>
        <path d="M100 146 l11 -9 h-22 z" fill="#0b1220"/>
      </svg>
      <span class="tap-caption">TAP TO EARN</span>
    </button>
    <div id="tap-floaters" class="tap-floaters" aria-hidden="true"></div>
  </div>
  <div class="card">
    <div class="row-between">
      <p class="card-title">Total earned</p>
      <p class="card-hint" id="home-total-earned">0 coins</p>
    </div>
    <p class="card-hint mt-8" id="home-tap-queue" hidden></p>
  </div>
</section>

<section class="screen" id="screen-tasks" data-screen="tasks" hidden>
  <h2 class="screen-title">Tasks</h2>
  <p class="screen-sub">Complete tasks to earn coins.</p>
  <div id="tasks-list" class="stack"><div class="skeleton-card"></div></div>
</section>

<section class="screen" id="screen-friends" data-screen="friends" hidden>
  <h2 class="screen-title">Invite Friends</h2>
  <div class="card">
    <p class="card-title">Your invite link</p>
    <div class="copy-row">
      <input id="ref-link-input" class="text-input" type="text" readonly value="Loading…"/>
      <button id="ref-copy-btn" class="btn btn-primary btn-compact" type="button">Copy</button>
    </div>
    <div class="row-between mt-12">
      <p class="card-hint">Valid referrals</p>
      <p class="ref-count-badge" id="ref-count-text">0</p>
    </div>
    <p class="card-hint mt-8" id="ref-eligibility-text">—</p>
  </div>
  <div class="card">
    <p class="card-title">Rewards</p>
    <p class="card-hint">Claim $10 at each milestone. Unlocks after 3 valid referrals.</p>
    <ul class="milestone-claim-list" id="ref-milestones"></ul>
  </div>
</section>

<section class="screen" id="screen-wallet" data-screen="wallet" hidden>
  <h2 class="screen-title">Wallet</h2>
  <div class="tabs" id="wallet-tabs">
    <button class="tab is-active" data-tab="add" type="button">Add Wallet</button>
    <button class="tab" data-tab="withdraw" type="button">Withdraw</button>
  </div>
  <div class="tab-panel" data-panel="add">
    <div id="wa-locked" class="card">
      <div class="lock-banner">
        <span class="lock-icon">🔒</span>
        <div>
          <p class="card-title">Add Wallet — <span id="wa-fee-header">$0.00 USD</span> Fee</p>
          <p class="card-hint mt-4">This section is currently locked by the administrator.</p>
        </div>
      </div>
    </div>
    <div id="wa-enabled" hidden>
      <div class="card">
        <p class="card-title">Add Wallet — <span id="wa-fee-header2">$0.00 USD</span> Fee</p>
        <p class="card-hint mt-8">Choose a payment method below.</p>
      </div>
      <div class="pay-methods" id="wa-methods"></div>
      <div id="wa-form-wrap" class="card" hidden>
        <div class="row-between">
          <p class="card-title" id="wa-form-title">Complete payment</p>
          <span class="pill pill-amber" id="wa-status-pill">pending</span>
        </div>
        <div class="deposit-instructions" id="wa-instructions"></div>
        <label class="field-label mt-12">Transaction screenshot</label>
        <label class="upload-zone" id="wa-upload-zone">
          <input id="wa-screenshot" type="file" accept="image/png,image/jpeg,image/webp"/>
          <span class="upload-icon">🖼️</span>
          <span class="upload-text" id="wa-upload-text">Tap to attach a screenshot</span>
          <span class="upload-hint">PNG / JPG / WEBP, up to 5 MB</span>
        </label>
        <div id="wa-preview-wrap" class="upload-preview" hidden>
          <img id="wa-preview-img" alt=""/>
          <button id="wa-preview-remove" class="upload-remove" type="button" aria-label="Remove">✕</button>
        </div>
        <label class="field-label mt-12" for="wa-txref">Transaction reference (optional)</label>
        <input id="wa-txref" class="text-input" type="text" placeholder="TX ID" autocomplete="off"/>
        <div id="wa-error" class="form-error" hidden></div>
        <button id="wa-submit" class="btn btn-primary mt-12" type="button">Confirm payment</button>
        <button id="wa-cancel" class="btn btn-ghost mt-8" type="button">Cancel</button>
      </div>
      <div class="card">
        <p class="card-title">My activation requests</p>
        <ul class="leader-list" id="wa-history"><li class="empty-state">No requests yet.</li></ul>
      </div>
    </div>
  </div>
  <div class="tab-panel" data-panel="withdraw" hidden>
    <div class="card">
      <div class="row-between">
        <p class="card-title">Withdrawal window</p>
        <span class="pill pill-cyan" id="wd-window-state">—</span>
      </div>
      <div class="timer-grid">
        <div class="timer-cell"><span class="timer-num" id="tm-days">00</span><span class="timer-label">Days</span></div>
        <div class="timer-cell"><span class="timer-num" id="tm-hours">00</span><span class="timer-label">Hours</span></div>
        <div class="timer-cell"><span class="timer-num" id="tm-minutes">00</span><span class="timer-label">Minutes</span></div>
        <div class="timer-cell"><span class="timer-num" id="tm-seconds">00</span><span class="timer-label">Seconds</span></div>
      </div>
      <p class="card-hint mt-8" id="wd-timer-note">—</p>
    </div>
    <div class="card balance-card">
      <p class="balance-label">Withdrawable balance</p>
      <p class="balance-value dollar-value"><span id="wd-available">$0.00</span></p>
      <div class="balance-split">
        <div><p class="mini-label">Coins</p><p class="mini-value" id="wd-coins">0</p></div>
        <div><p class="mini-label">Wallet</p><p class="mini-value" id="wd-wallet-status">—</p></div>
        <div><p class="mini-label">Min</p><p class="mini-value" id="wd-min">$0.00</p></div>
      </div>
    </div>
    <div class="card">
      <p class="card-title">Request withdrawal</p>
      <label class="field-label mt-12" for="wd-method">Method</label>
      <select id="wd-method" class="text-input"></select>
      <label class="field-label mt-12" for="wd-amount">Amount (USD)</label>
      <input id="wd-amount" class="text-input" type="number" min="0" step="0.01" placeholder="0.00"/>
      <label class="field-label mt-12" for="wd-destination">Destination</label>
      <input id="wd-destination" class="text-input" type="text" placeholder="Wallet address / Pay ID" autocomplete="off"/>
      <p class="card-hint mt-8" id="wd-eligibility">—</p>
      <div id="wd-error" class="form-error" hidden></div>
      <button id="wd-submit" class="btn btn-primary mt-12" type="button">Submit withdrawal request</button>
    </div>
    <div class="card">
      <p class="card-title">Withdrawal history</p>
      <ul class="leader-list" id="wd-list"><li class="empty-state">No requests yet.</li></ul>
    </div>
  </div>
</section>

<section class="screen" id="screen-profile" data-screen="profile" hidden>
  <h2 class="screen-title">Profile</h2>
  <div class="card profile-card">
    <div class="avatar avatar-lg" id="profile-avatar"><span id="profile-avatar-fallback">•</span></div>
    <div class="profile-meta">
      <p class="profile-name" id="profile-name">—</p>
      <p class="profile-sub" id="profile-username">—</p>
      <p class="profile-sub" id="profile-id">—</p>
    </div>
  </div>
  <div class="card balance-card">
    <p class="balance-label">Balances</p>
    <div class="balance-split">
      <div><p class="mini-label">Coins</p><p class="mini-value" id="profile-coins">0</p></div>
      <div><p class="mini-label">Dollars</p><p class="mini-value" id="profile-dollars">$0.00</p></div>
      <div><p class="mini-label">Referrals</p><p class="mini-value" id="profile-refs">0</p></div>
    </div>
  </div>
  <div class="card">
    <p class="card-title">Wallet</p>
    <button class="list-btn wallet-entry" type="button" id="open-wallet-btn">
      <span>💳 Open Wallet</span>
      <span class="wallet-entry-status" id="profile-wallet-status">Inactive</span>
    </button>
  </div>
  <div class="card">
    <p class="card-title">More</p>
    <button class="list-btn" type="button" data-goto="transactions">📜 Transaction history</button>
    <button class="list-btn" type="button" id="reload-app-btn">🔄 Reload app</button>
  </div>
  <p class="disclaimer">Coins are internal points. Dollar balances are internal ledger entries.</p>
</section>

<section class="screen" id="screen-transactions" data-screen="transactions" hidden>
  <h2 class="screen-title">Transactions</h2>
  <ul class="tx-list" id="tx-list"><li class="empty-state">Loading…</li></ul>
  <button id="tx-more-btn" class="btn btn-ghost mt-12" type="button" hidden>Load more</button>
</section>
</main>

<nav class="bottom-nav nav-4" id="bottom-nav" aria-label="Main navigation">
  <button class="nav-btn is-active" type="button" data-nav="home"><svg viewBox="0 0 24 24"><path d="M3 10.5 12 3l9 7.5V21a1 1 0 0 1-1 1h-5v-7H9v7H4a1 1 0 0 1-1-1z" fill="none" stroke="currentColor" stroke-width="1.9" stroke-linejoin="round"/></svg><span>Home</span></button>
  <button class="nav-btn" type="button" data-nav="tasks"><svg viewBox="0 0 24 24"><path d="M9 5h11M9 12h11M9 19h11M4 5l1.4 1.4L8 3.8M4 12l1.4 1.4L8 10.8M4 19l1.4 1.4L8 17.8" fill="none" stroke="currentColor" stroke-width="1.9" stroke-linecap="round" stroke-linejoin="round"/></svg><span>Tasks</span></button>
  <button class="nav-btn" type="button" data-nav="friends"><svg viewBox="0 0 24 24"><circle cx="9" cy="8" r="3.2" fill="none" stroke="currentColor" stroke-width="1.9"/><path d="M2.5 20a6.5 6.5 0 0 1 13 0M16.5 5.2a3.2 3.2 0 0 1 0 6M18 20a6.5 6.5 0 0 0-2-4.7" fill="none" stroke="currentColor" stroke-width="1.9" stroke-linecap="round"/></svg><span>Friends</span></button>
  <button class="nav-btn" type="button" data-nav="profile"><svg viewBox="0 0 24 24"><circle cx="12" cy="8" r="3.6" fill="none" stroke="currentColor" stroke-width="1.9"/><path d="M4.5 20.5a7.5 7.5 0 0 1 15 0" fill="none" stroke="currentColor" stroke-width="1.9" stroke-linecap="round"/></svg><span>Profile</span></button>
</nav>
</div>

<div id="toast-host" class="toast-host" aria-live="polite"></div>
<div id="boot-loader" class="boot-loader">
  <svg class="boot-fox" viewBox="0 0 200 200">
    <polygon points="40,72 28,14 86,50" fill="#ff8a3d"/><polygon points="160,72 172,14 114,50" fill="#ff8a3d"/>
    <path d="M100 40 L166 76 L150 136 L100 172 L50 136 L34 76 Z" fill="#ff8a3d"/>
    <path d="M100 106 L136 131 L100 168 L64 131 Z" fill="#fff3e6"/>
    <circle cx="72" cy="101" r="8.5" fill="#0b1220"/><circle cx="128" cy="101" r="8.5" fill="#0b1220"/>
  </svg>
  <p class="boot-text">Starting FOX EARN…</p>
</div>

<script src="/assets/js/config.js"></script>
<script src="/assets/js/api.js"></script>
<script src="/assets/js/telegram.js"></script>
<script src="/assets/js/ui.js"></script>
<script src="/assets/js/home.js"></script>
<script src="/assets/js/tasks.js"></script>
<script src="/assets/js/referrals.js"></script>
<script src="/assets/js/wallet.js"></script>
<script src="/assets/js/profile.js"></script>
<script src="/assets/js/app.js"></script>
</body>
</html>
'''

FILES["frontend/assets/js/config.js"] = r'''// Empty API_BASE_URL = same origin as backend. Perfect for unified deployment.
window.FOX_CONFIG = {
  API_BASE_URL: "",
  APP_NAME: "FOX EARN",
  REQUEST_TIMEOUT_MS: 15000,
  TAP_BATCH_SIZE: 10,
  TAP_FLUSH_INTERVAL_MS: 1200,
  TAP_MAX_LOCAL_QUEUE: 60,
  TOKEN_STORAGE_KEY: "fox_earn_session_token_v1",
  HEALTH_RETRY_MS: 8000
};
'''

FILES["frontend/assets/js/api.js"] = r'''(function(){
"use strict";
const CFG = window.FOX_CONFIG;
class ApiError extends Error{ constructor(m,s,c,d){ super(m); this.name="ApiError"; this.status=s||0; this.code=c||"unknown_error"; this.details=d||null; } }
const state={ token:null, online:true, onUnauthorized:null };

function loadToken(){ try{ state.token=localStorage.getItem(CFG.TOKEN_STORAGE_KEY)||null; }catch(e){ state.token=null; } return state.token; }
function setToken(t){ state.token=t||null; try{ if(t) localStorage.setItem(CFG.TOKEN_STORAGE_KEY,t); else localStorage.removeItem(CFG.TOKEN_STORAGE_KEY); }catch(e){} }
function clearToken(){ setToken(null); }
function getToken(){ return state.token; }

function apiUrl(p){
  const b=String(CFG.API_BASE_URL||"").replace(/\/+$/,"");
  const s=p.startsWith("/")?p:"/"+p;
  return b+s;
}
function isConfigured(){
  const b=String(CFG.API_BASE_URL||"");
  if(b.length===0) return true;  // same-origin is always fine
  return b.indexOf("REPLACE_WITH_YOUR_BACKEND_URL")===-1;
}

async function request(method,path,body,options){
  const opts=options||{};
  if(!isConfigured()) throw new ApiError("Backend URL not configured.",0,"not_configured");
  const ctrl=new AbortController();
  const timer=setTimeout(()=>ctrl.abort(), CFG.REQUEST_TIMEOUT_MS);
  const headers={"Accept":"application/json"};
  if(body!==undefined && body!==null) headers["Content-Type"]="application/json";
  if(state.token && !opts.skipAuth) headers["Authorization"]="Bearer "+state.token;
  if(opts.idempotencyKey) headers["Idempotency-Key"]=opts.idempotencyKey;
  headers["ngrok-skip-browser-warning"]="true";
  let r;
  try{
    r=await fetch(apiUrl(path),{method,headers,
      body:(body!==undefined&&body!==null)?JSON.stringify(body):undefined,
      signal:ctrl.signal,cache:"no-store",credentials:"omit",mode:"cors"});
    state.online=true;
  } catch(err){
    clearTimeout(timer); state.online=false;
    if(err&&err.name==="AbortError") throw new ApiError("Server took too long.",0,"timeout");
    throw new ApiError("Cannot reach server.",0,"network_error");
  }
  clearTimeout(timer);
  let payload=null;
  const text=await r.text().catch(()=>"");
  if(text){ try{ payload=JSON.parse(text); }catch(e){ payload={detail:text.slice(0,400)}; } }
  if(!r.ok){
    const detail=payload&&payload.detail;
    let message="Request failed.", code="http_"+r.status;
    if(typeof detail==="string") message=detail;
    else if(detail&&typeof detail==="object"){ message=detail.message||detail.msg||message; code=detail.code||code; }
    else if(Array.isArray(detail)&&detail.length){
      const f=detail[0]||{}; const loc=Array.isArray(f.loc)?f.loc.join("."):"";
      message=(loc?loc+": ":"")+(f.msg||"Invalid input."); code="validation_error";
    }
    if(r.status===401){ clearToken(); if(typeof state.onUnauthorized==="function") state.onUnauthorized(); }
    throw new ApiError(message,r.status,code,payload);
  }
  return payload;
}

window.Fox=window.Fox||{};
window.Fox.api={
  ApiError, loadToken, setToken, getToken, clearToken, isConfigured,
  setUnauthorizedHandler(fn){ state.onUnauthorized=fn; },
  isOnline(){ return state.online; },
  get(p,o){ return request("GET",p,undefined,o); },
  post(p,b,o){ return request("POST",p,b,o); },
  patch(p,b,o){ return request("PATCH",p,b,o); },
  del(p,o){ return request("DELETE",p,undefined,o); },
  health(){ return request("GET","/health",undefined,{skipAuth:true}); },
  authenticate(initData){ return request("POST","/api/auth/telegram",{init_data:initData},{skipAuth:true}); }
};
})();
'''

FILES["frontend/assets/js/telegram.js"] = r'''(function(){
"use strict";
const tg = (window.Telegram && window.Telegram.WebApp) ? window.Telegram.WebApp : null;
const state={ available:!!tg, initData:"", user:null, startParam:"", colorScheme:"dark", version:"0" };
function init(){
  if(!tg) return {available:false, initData:"", user:null, startParam:""};
  try{ tg.ready(); }catch(e){}
  try{ tg.expand(); }catch(e){}
  try{ if(typeof tg.disableVerticalSwipes==="function") tg.disableVerticalSwipes(); }catch(e){}
  try{ if(typeof tg.setHeaderColor==="function") tg.setHeaderColor("#070d1b"); if(typeof tg.setBackgroundColor==="function") tg.setBackgroundColor("#070d1b"); }catch(e){}
  state.initData=tg.initData||"";
  state.version=String(tg.version||"0");
  state.colorScheme=tg.colorScheme||"dark";
  state.startParam=(tg.initDataUnsafe&&tg.initDataUnsafe.start_param)||"";
  if(tg.initDataUnsafe&&tg.initDataUnsafe.user) state.user=tg.initDataUnsafe.user;
  return { available:true, initData:state.initData, user:state.user, startParam:state.startParam };
}
function hasValidInitData(){ return typeof state.initData==="string" && state.initData.length>20 && state.initData.indexOf("hash=")!==-1; }
function isInsideTelegram(){ return state.available && hasValidInitData(); }
function hapticImpact(s){ if(!tg||!tg.HapticFeedback)return; try{ tg.HapticFeedback.impactOccurred(s||"light"); }catch(e){} }
function hapticNotify(t){ if(!tg||!tg.HapticFeedback)return; try{ tg.HapticFeedback.notificationOccurred(t||"success"); }catch(e){} }
function openLink(u,tryIV){ if(!u)return; if(tg&&typeof tg.openLink==="function"){ try{ tg.openLink(u,{try_instant_view:!!tryIV}); return; }catch(e){} } window.open(u,"_blank","noopener,noreferrer"); }
function openTelegramLink(u){ if(!u)return; if(tg&&typeof tg.openTelegramLink==="function"){ try{ tg.openTelegramLink(u); return; }catch(e){} } window.open(u,"_blank","noopener,noreferrer"); }
function shareUrl(u,t){ const s="https://t.me/share/url?url="+encodeURIComponent(u)+"&text="+encodeURIComponent(t||""); openTelegramLink(s); }
function getDisplayName(){ const u=state.user; if(!u)return ""; const f=[u.first_name,u.last_name].filter(Boolean).join(" ").trim(); return f||u.username||""; }
function getPhotoUrl(){ const u=state.user; return (u&&u.photo_url)?u.photo_url:""; }
window.Fox=window.Fox||{};
window.Fox.tg={ init, state, isInsideTelegram, hasValidInitData, hapticImpact, hapticNotify, openLink, openTelegramLink, shareUrl, getDisplayName, getPhotoUrl };
})();
'''

FILES["frontend/assets/js/ui.js"] = r'''(function(){
"use strict";
const el={};
function cache(){ el.view=document.getElementById("view"); el.bottomNav=document.getElementById("bottom-nav"); el.backBtn=document.getElementById("back-btn"); el.refreshBtn=document.getElementById("refresh-btn"); el.toastHost=document.getElementById("toast-host"); el.banner=document.getElementById("status-banner"); el.bannerText=document.getElementById("status-banner-text"); el.bootLoader=document.getElementById("boot-loader"); }
function escapeHtml(v){ if(v===null||v===undefined)return ""; return String(v).replace(/&/g,"&amp;").replace(/</g,"&lt;").replace(/>/g,"&gt;").replace(/"/g,"&quot;").replace(/'/g,"&#39;"); }
function formatNumber(v){ const n=Number(v); if(!isFinite(n))return "0"; return n.toLocaleString("en-US"); }
function formatUSD(cents){ const n=Number(cents||0)/100; if(!isFinite(n))return "$0.00"; return "$"+n.toFixed(2); }
function formatDate(iso){ if(!iso)return "—"; const d=new Date(iso); if(isNaN(d.getTime()))return "—"; const M=["Jan","Feb","Mar","Apr","May","Jun","Jul","Aug","Sep","Oct","Nov","Dec"]; return d.getDate()+" "+M[d.getMonth()]+" "+d.getFullYear(); }
function formatDateTime(iso){ if(!iso)return "—"; const d=new Date(iso); if(isNaN(d.getTime()))return "—"; const hh=String(d.getHours()).padStart(2,"0"); const mm=String(d.getMinutes()).padStart(2,"0"); return formatDate(iso)+" · "+hh+":"+mm; }
function toast(message,kind,durationMs){ if(!el.toastHost)return; const t=kind||"info"; const n=document.createElement("div"); n.className="toast toast-"+t; n.textContent=String(message); el.toastHost.appendChild(n); const life=durationMs||(t==="error"?4200:2600); setTimeout(()=>{ n.classList.add("out"); setTimeout(()=>{ if(n.parentNode) n.parentNode.removeChild(n); },260); },life); }
function showBanner(text,kind){ if(!el.banner||!el.bannerText)return; el.bannerText.textContent=text; el.banner.setAttribute("data-kind",kind||"ok"); el.banner.hidden=false; }
function hideBanner(){ if(el.banner) el.banner.hidden=true; }
function hideBootLoader(){ if(el.bootLoader) el.bootLoader.classList.add("is-hidden"); }
const SUB_SCREENS=["transactions","wallet"];
let currentScreen="home", previousScreen="home";
function showScreen(name){
  const target=document.getElementById("screen-"+name); if(!target) return;
  if(name!==currentScreen){ previousScreen=currentScreen; currentScreen=name; }
  document.querySelectorAll(".screen").forEach(s=>{ s.hidden=(s.id!=="screen-"+name); });
  const isSub=SUB_SCREENS.indexOf(name)!==-1;
  if(el.bottomNav) el.bottomNav.hidden=isSub;
  if(el.backBtn) el.backBtn.hidden=!isSub;
  if(el.bottomNav&&!isSub) el.bottomNav.querySelectorAll(".nav-btn").forEach(b=>b.classList.toggle("is-active",b.getAttribute("data-nav")===name));
  if(el.view) el.view.scrollTop=0; window.scrollTo(0,0);
  const hooks=window.Fox.screenHooks||{}; if(typeof hooks[name]==="function"){ try{ hooks[name](); }catch(e){} }
}
function goBack(){ showScreen(previousScreen&&previousScreen!==currentScreen?previousScreen:"home"); }
function setLoading(btn,loading,text){ if(!btn)return; if(loading){ if(!btn.dataset.originalText) btn.dataset.originalText=btn.textContent; btn.disabled=true; btn.textContent=text||"Please wait…"; } else { btn.disabled=false; if(btn.dataset.originalText){ btn.textContent=btn.dataset.originalText; delete btn.dataset.originalText; } } }
window.Fox=window.Fox||{};
window.Fox.ui={ init:cache, el, escapeHtml, formatNumber, formatUSD, formatDate, formatDateTime, toast, showBanner, hideBanner, hideBootLoader, showScreen, goBack, setLoading };
})();
'''

FILES["frontend/assets/js/home.js"] = r'''(function(){
"use strict";
const CFG=window.FOX_CONFIG, U=window.Fox.ui, API=window.Fox.api, TG=window.Fox.tg;
const tap={ pending:0, inFlight:false, flushTimer:null, button:null, floaters:null };

function setText(id,v){ const n=document.getElementById(id); if(n) n.textContent=v; }

function renderAvatar(boxId,fbId,u){
  const box=document.getElementById(boxId); if(!box) return;
  const photo = u.photo_url || TG.getPhotoUrl();
  const name = u.display_name || TG.getDisplayName() || "•";
  if(photo) box.innerHTML='<img src="'+U.escapeHtml(photo)+'" alt="" referrerpolicy="no-referrer"/>';
  else box.innerHTML='<span id="'+fbId+'">'+U.escapeHtml((name).trim().charAt(0).toUpperCase())+"</span>";
}

function renderSummary(data){
  const u=data.user||{}, s=data.stats||{};
  setText("home-name", u.display_name||"—");
  setText("home-username", u.username?"@"+u.username:"—");
  setText("home-coins", U.formatNumber(s.balance||0));
  setText("home-dollars", U.formatUSD(s.dollar_balance_cents||0));
  setText("home-total-earned", U.formatNumber(s.total_earned||0)+" coins");
  renderAvatar("home-avatar","home-avatar-fallback",u);
}

function renderPreview(){
  setText("home-name","—");
  setText("home-username","Open inside Telegram to sign in");
  setText("home-coins","0");
  setText("home-dollars","$0.00");
  setText("home-total-earned","0 coins");
  const box=document.getElementById("home-avatar");
  if(box) box.innerHTML='<span id="home-avatar-fallback">•</span>';
}

function spawnFloater(e,text){
  if(!tap.floaters) return;
  const n=document.createElement("span"); n.className="floater"; n.textContent=text;
  const r=tap.floaters.getBoundingClientRect();
  let x=r.width/2,y=r.height/2;
  if(e && typeof e.clientX==="number" && e.clientX>0){ x=e.clientX-r.left; y=e.clientY-r.top; }
  else { x+=(Math.random()-.5)*r.width*.45; y+=(Math.random()-.5)*r.height*.35; }
  n.style.left=x+"px"; n.style.top=y+"px";
  tap.floaters.appendChild(n);
  setTimeout(()=>{ if(n.parentNode) n.parentNode.removeChild(n); },1000);
}

function updateQueueLabel(){
  const n=document.getElementById("home-tap-queue"); if(!n) return;
  if(tap.pending>0 || tap.inFlight){ n.hidden=false; n.textContent = tap.inFlight ? "Syncing taps…" : tap.pending+" tap(s) queued…"; }
  else n.hidden=true;
}

function newBatchId(){ return "tap_"+Date.now().toString(36)+"_"+Math.random().toString(36).slice(2,12); }

function onTap(e){
  if(!window.Fox.state.authenticated){ U.toast("Open inside Telegram.","info"); spawnFloater(e,"+0"); return; }
  tap.pending+=1; spawnFloater(e,"+1"); TG.hapticImpact("light");
  tap.button.classList.add("is-tapped"); setTimeout(()=>tap.button.classList.remove("is-tapped"),90);
  updateQueueLabel();
  if(tap.pending>=CFG.TAP_BATCH_SIZE) flushTaps();
  else if(!tap.flushTimer) tap.flushTimer=setTimeout(flushTaps,CFG.TAP_FLUSH_INTERVAL_MS);
}

function applyTapResult(res){
  if(!res) return;
  if(typeof res.balance==="number") setText("home-coins", U.formatNumber(res.balance));
  if(typeof res.dollar_balance_cents==="number") setText("home-dollars", U.formatUSD(res.dollar_balance_cents));
  if(typeof res.total_earned==="number") setText("home-total-earned", U.formatNumber(res.total_earned)+" coins");
}

async function flushTaps(){
  if(tap.flushTimer){ clearTimeout(tap.flushTimer); tap.flushTimer=null; }
  if(tap.inFlight || tap.pending<=0) return;
  if(!window.Fox.state.authenticated){ tap.pending=0; updateQueueLabel(); return; }
  const count = Math.min(tap.pending, CFG.TAP_MAX_LOCAL_QUEUE);
  tap.pending -= count; tap.inFlight = true;
  const batchId = newBatchId(); updateQueueLabel();
  try{ const res = await API.post("/api/taps",{taps:count,batch_id:batchId}); applyTapResult(res); TG.hapticImpact("light"); }
  catch(err){
    tap.pending = Math.min(tap.pending+count, CFG.TAP_MAX_LOCAL_QUEUE);
    if(err && err.status===429) U.toast("Too fast.","info");
    else if(err && err.status===401) tap.pending=0;
    else U.showBanner("Connection problem.","offline");
  } finally {
    tap.inFlight=false; updateQueueLabel();
    if(tap.pending>0 && !tap.flushTimer) tap.flushTimer=setTimeout(flushTaps, CFG.TAP_FLUSH_INTERVAL_MS);
  }
}

function initTapButton(){
  tap.button = document.getElementById("tap-button");
  tap.floaters = document.getElementById("tap-floaters");
  if(tap.button) tap.button.addEventListener("click", onTap, {passive:true});
}

async function load(){
  if(!window.Fox.state.authenticated){ renderPreview(); return; }
  try{ const data = await API.get("/api/profile"); window.Fox.state.profile=data; renderSummary(data); U.hideBanner(); }
  catch(err){ if(err && err.status===401) return; U.showBanner("Backend unavailable.","offline"); }
}

window.Fox = window.Fox || {};
window.Fox.home = { load, initTapButton, flushTaps };
})();
'''

FILES["frontend/assets/js/tasks.js"] = r'''(function(){
"use strict";
const U=window.Fox.ui, API=window.Fox.api;

function renderPreview(){
  const host=document.getElementById("tasks-list"); if(!host) return;
  host.innerHTML='<div class="card"><p class="empty-state">No tasks available right now.</p></div>';
}

async function load(){
  const host=document.getElementById("tasks-list"); if(!host) return;
  if(!window.Fox.state.authenticated){ renderPreview(); return; }
  host.innerHTML='<div class="skeleton-card"></div>';
  try{
    const res=await API.get("/api/tasks"); const tasks=res.tasks||[];
    if(!tasks.length){ host.innerHTML='<div class="card"><p class="empty-state">No tasks available right now.</p></div>'; return; }
  } catch(err){ host.innerHTML='<div class="card"><p class="empty-state">'+U.escapeHtml(err.message||"Could not load tasks.")+"</p></div>"; }
}

window.Fox=window.Fox||{}; window.Fox.screenHooks=window.Fox.screenHooks||{};
window.Fox.screenHooks.tasks=()=>load();
window.Fox.tasks={ load };
})();
'''

FILES["frontend/assets/js/referrals.js"] = r'''(function(){
"use strict";
const U=window.Fox.ui, API=window.Fox.api, TG=window.Fox.tg;
let loaded=false;
function setText(id,v){ const n=document.getElementById(id); if(n) n.textContent=v; }

function renderPreview(){
  const input=document.getElementById("ref-link-input"); if(input) input.value="Open inside Telegram";
  setText("ref-count-text","0");
  setText("ref-eligibility-text","Open inside Telegram to see your referrals.");
  const host=document.getElementById("ref-milestones");
  if(host) host.innerHTML='<li class="empty-state">Open inside Telegram.</li>';
}

function render(data){
  const link=data.referral_link||"";
  const input=document.getElementById("ref-link-input"); if(input) input.value=link||"—";
  const valid=Number(data.valid_referrals||0);
  const minReq=Number(data.min_referrals_to_unlock||3);
  const unlocked = valid >= minReq;
  setText("ref-count-text", U.formatNumber(valid));
  setText("ref-eligibility-text", unlocked ? "🎉 Reward claims unlocked." : "You need "+minReq+" valid referrals. "+Math.max(0,minReq-valid)+" more to go.");

  const host=document.getElementById("ref-milestones"); if(!host) return;
  const ms=data.milestones||[];
  if(!ms.length){ host.innerHTML='<li class="empty-state">No milestones configured.</li>'; return; }
  host.innerHTML = ms.map(m=>{
    const claimed=!!m.claimed, qualified=valid>=Number(m.count);
    let state,label,disabled;
    if(claimed){ state="claimed"; label="Claimed"; disabled=true; }
    else if(!unlocked){ state="locked"; label="Locked"; disabled=true; }
    else if(!qualified){ state="not_qualified"; label="Not yet"; disabled=true; }
    else { state="available"; label="Claim $"+(Number(m.reward_cents||0)/100).toFixed(2); disabled=false; }
    return '<li><div class="ms-left">'+
      '<span class="ms-title">'+U.escapeHtml(String(m.count))+' '+(Number(m.count)===1?"Invite":"Invites")+'</span>'+
      '<span class="ms-reward">$'+(Number(m.reward_cents||0)/100).toFixed(2)+'</span>'+
      '<span class="ms-status">'+U.escapeHtml(
        state==="locked"?("Requires "+minReq+" valid referrals"):
        state==="not_qualified"?("Reach "+m.count+" valid referrals"):
        state==="claimed"?"Already claimed":"Ready to claim")+'</span></div>'+
      '<button class="btn '+(state==="available"?"btn-primary":"btn-ghost")+' btn-compact ms-btn" '+
        (disabled?"disabled ":"")+'data-claim="'+m.count+'" data-state="'+state+'">'+label+'</button></li>';
  }).join("");
  host.querySelectorAll("[data-claim]").forEach(b=>{
    if(b.dataset.state!=="available") return;
    b.addEventListener("click",()=>claimMilestone(b));
  });
}

async function claimMilestone(btn){
  const count=btn.getAttribute("data-claim");
  if(!window.confirm("Claim $10 for the "+count+"-invite milestone?")) return;
  U.setLoading(btn,true,"Claiming…");
  try{
    const res = await API.post("/api/referrals/claim",{milestone:parseInt(count,10)});
    U.toast("Claimed $"+(Number(res.reward_cents||0)/100).toFixed(2)+"!","success"); TG.hapticNotify("success");
    await load(true); if(window.Fox.home) window.Fox.home.load();
  } catch(err){ U.toast(err.message||"Could not claim.","error"); U.setLoading(btn,false); }
}

function initCopy(){
  const btn=document.getElementById("ref-copy-btn"), input=document.getElementById("ref-link-input");
  if(!btn||!input || btn.dataset.bound==="1") return; btn.dataset.bound="1";
  btn.addEventListener("click", async ()=>{
    if(!window.Fox.state.authenticated){ U.toast("Open inside Telegram.","info"); return; }
    const v=input.value;
    if(!v || v==="—" || v==="Loading…"){ U.toast("Link not ready.","error"); return; }
    try{
      if(navigator.clipboard && navigator.clipboard.writeText) await navigator.clipboard.writeText(v);
      else { input.removeAttribute("readonly"); input.select(); input.setSelectionRange(0,99999); document.execCommand("copy"); input.setAttribute("readonly","readonly"); }
      U.toast("Copied!","success"); TG.hapticNotify("success");
    } catch(e){ U.toast("Copy failed.","error"); }
  });
}

async function load(force){
  if(loaded && !force) return;
  if(!window.Fox.state.authenticated){ renderPreview(); loaded=true; return; }
  try{ const d=await API.get("/api/referrals"); render(d); loaded=true; }
  catch(err){ const h=document.getElementById("ref-milestones"); if(h) h.innerHTML='<li class="empty-state">'+U.escapeHtml(err.message||"Could not load.")+"</li>"; }
}

window.Fox=window.Fox||{}; window.Fox.screenHooks=window.Fox.screenHooks||{};
window.Fox.screenHooks.friends=()=>{ initCopy(); load(false); };
window.Fox.referrals={ load, initCopy };
})();
'''

FILES["frontend/assets/js/wallet.js"] = r'''(function(){
"use strict";
const U=window.Fox.ui, API=window.Fox.api, TG=window.Fox.tg;
let loaded=false, walletState=null;
let activeActivation=null, pendingScreenshot=null, withdrawTimerId=null;
const MAX_BYTES = 5 * 1024 * 1024;

function setText(id,v){ const n=document.getElementById(id); if(n) n.textContent=v; }
function showError(id,m){ const b=document.getElementById(id); if(!b) return; if(m){ b.textContent=m; b.hidden=false; } else { b.hidden=true; b.textContent=""; } }

function initTabs(){
  document.querySelectorAll("#wallet-tabs .tab").forEach(t=>{
    if(t.dataset.bound==="1") return; t.dataset.bound="1";
    t.addEventListener("click",()=>{
      document.querySelectorAll("#wallet-tabs .tab").forEach(x=>x.classList.remove("is-active"));
      t.classList.add("is-active");
      const tab=t.getAttribute("data-tab");
      document.querySelectorAll("#screen-wallet .tab-panel").forEach(p=>{ p.hidden = p.getAttribute("data-panel")!==tab; });
      TG.hapticImpact("light");
    });
  });
}

function renderPreview(){
  const locked=document.getElementById("wa-locked");
  const enabled=document.getElementById("wa-enabled");
  if(locked){ locked.hidden=false; }
  if(enabled) enabled.hidden=true;
  setText("wa-fee-header","$20.00 USD"); setText("wa-fee-header2","$20.00 USD");
  setText("wd-available","$0.00"); setText("wd-coins","0"); setText("wd-wallet-status","—"); setText("wd-min","$0.00");
  const sel=document.getElementById("wd-method");
  if(sel){ sel.innerHTML=""; const o=document.createElement("option"); o.value=""; o.textContent="—"; sel.appendChild(o); sel.disabled=true; }
  setTimerDisplay(0);
}

function renderMethods(methods){
  const host=document.getElementById("wa-methods"); if(!host) return;
  if(!methods.length){ host.innerHTML='<div class="card"><p class="empty-state">No payment methods enabled.</p></div>'; return; }
  host.innerHTML = methods.map(m=>{
    const cls = m.code==="okx" ? "okx" : m.code==="bybit" ? "bybit" : "binance";
    const initials = m.code.slice(0,2).toUpperCase();
    return '<button class="pay-card" data-method="'+U.escapeHtml(m.code)+'" type="button">'+
      '<span class="pay-logo '+cls+'">'+U.escapeHtml(initials)+'</span>'+
      '<span class="pay-info"><span class="pay-name">'+U.escapeHtml(m.label)+'</span>'+
      '<span class="pay-fee">$'+(Number(m.fee_cents||0)/100).toFixed(2)+' USD</span></span>'+
      '<span class="pay-arrow">›</span></button>';
  }).join("");
  host.querySelectorAll("[data-method]").forEach(b=>b.addEventListener("click",()=>selectMethod(b.getAttribute("data-method"))));
}

function selectMethod(code){
  const methods=(walletState && walletState.wallet_methods) || [];
  const m=methods.find(x=>x.code===code); if(!m) return;
  const form=document.getElementById("wa-form-wrap");
  const instr=document.getElementById("wa-instructions");
  const title=document.getElementById("wa-form-title");
  activeActivation={ method:code, fee_cents:m.fee_cents||0, label:m.label };
  document.querySelectorAll("#wa-methods .pay-card").forEach(p=>p.classList.toggle("is-selected", p.getAttribute("data-method")===code));
  if(title) title.textContent="Pay with "+m.label;
  if(instr){
    const lines=[];
    lines.push("<p><b>Amount:</b> $"+((m.fee_cents||0)/100).toFixed(2)+" USD</p>");
    if(m.instructions) lines.push("<p class='mt-8'>"+U.escapeHtml(m.instructions)+"</p>");
    if(m.destination) lines.push("<p class='mt-8'><b>Destination:</b> <code>"+U.escapeHtml(m.destination)+"</code></p>");
    instr.innerHTML=lines.join("");
  }
  if(form) form.hidden=false;
  TG.hapticImpact("light");
  form.scrollIntoView({behavior:"smooth",block:"start"});
}

function resetScreenshot(){
  pendingScreenshot=null;
  const input=document.getElementById("wa-screenshot"); if(input) input.value="";
  const img=document.getElementById("wa-preview-img"); if(img) img.removeAttribute("src");
  const wrap=document.getElementById("wa-preview-wrap"); if(wrap) wrap.hidden=true;
  const zone=document.getElementById("wa-upload-zone"); if(zone) zone.classList.remove("has-file");
  const txt=document.getElementById("wa-upload-text"); if(txt) txt.textContent="Tap to attach a screenshot";
}

function initScreenshot(){
  const input=document.getElementById("wa-screenshot");
  const zone=document.getElementById("wa-upload-zone");
  const wrap=document.getElementById("wa-preview-wrap");
  const img=document.getElementById("wa-preview-img");
  const txt=document.getElementById("wa-upload-text");
  const rm=document.getElementById("wa-preview-remove");
  if(!input || input.dataset.bound==="1") return;
  input.dataset.bound="1";
  input.addEventListener("change",()=>{
    const file=input.files && input.files[0]; if(!file) return;
    if(!/^image\/(png|jpeg|jpg|webp)$/i.test(file.type)){ U.toast("PNG, JPG or WEBP only.","error"); resetScreenshot(); return; }
    if(file.size>MAX_BYTES){ U.toast("Max 5 MB.","error"); resetScreenshot(); return; }
    const r=new FileReader();
    r.onload=()=>{
      pendingScreenshot={ dataUrl:String(r.result), name:file.name };
      if(img) img.src=pendingScreenshot.dataUrl;
      if(wrap) wrap.hidden=false;
      if(zone) zone.classList.add("has-file");
      if(txt) txt.textContent="Screenshot attached ✓";
      TG.hapticImpact("light");
    };
    r.onerror=()=>{ U.toast("Could not read image.","error"); resetScreenshot(); };
    r.readAsDataURL(file);
  });
  if(rm) rm.addEventListener("click",(e)=>{ e.preventDefault(); e.stopPropagation(); resetScreenshot(); });
}

async function submitActivation(){
  showError("wa-error","");
  if(!activeActivation){ U.toast("Select a payment method first.","info"); return; }
  if(!pendingScreenshot){ showError("wa-error","Attach a payment screenshot."); return; }
  const tref=document.getElementById("wa-txref");
  const btn=document.getElementById("wa-submit");
  U.setLoading(btn,true,"Submitting…");
  try{
    const res=await API.post("/api/wallet/activate/submit",{
      method:activeActivation.method,
      tx_ref: tref ? tref.value.trim() : "",
      screenshot_base64: pendingScreenshot.dataUrl
    });
    U.toast("Submitted. Request #"+res.id+" pending.","success");
    TG.hapticNotify("success");
    activeActivation=null; resetScreenshot();
    const form=document.getElementById("wa-form-wrap"); if(form) form.hidden=true;
    await load(true);
  } catch(err){ showError("wa-error",err.message||"Submission failed."); }
  finally { U.setLoading(btn,false); }
}

function renderActivations(list){
  const host=document.getElementById("wa-history"); if(!host) return;
  if(!list.length){ host.innerHTML='<li class="empty-state">No requests yet.</li>'; return; }
  const P={pending:'<span class="pill pill-amber">Pending</span>',approved:'<span class="pill pill-green">Approved</span>',rejected:'<span class="pill pill-red">Rejected</span>'};
  host.innerHTML=list.map(a=>'<li><span class="li-main">'+
    '<span class="li-name">'+U.escapeHtml(a.method.toUpperCase())+" · $"+((Number(a.fee_cents||0)/100).toFixed(2))+'</span>'+
    '<span class="li-sub">'+U.escapeHtml(U.formatDateTime(a.created_at))+'</span></span>'+
    (P[a.status]||'<span class="pill pill-muted">'+U.escapeHtml(a.status)+'</span>')+"</li>").join("");
}

function renderWithdrawals(reqs){
  const host=document.getElementById("wd-list"); if(!host) return;
  if(!reqs.length){ host.innerHTML='<li class="empty-state">No requests yet.</li>'; return; }
  const P={pending:'<span class="pill pill-amber">Pending</span>',approved:'<span class="pill pill-cyan">Approved</span>',rejected:'<span class="pill pill-red">Rejected</span>',paid:'<span class="pill pill-green">Paid</span>'};
  host.innerHTML=reqs.map(r=>'<li><span class="li-main">'+
    '<span class="li-name">'+U.formatUSD(r.amount_cents)+" · "+U.escapeHtml(r.method)+'</span>'+
    '<span class="li-sub">'+U.escapeHtml(U.formatDateTime(r.created_at))+'</span></span>'+
    (P[r.status]||'<span class="pill pill-muted">'+U.escapeHtml(r.status)+'</span>')+"</li>").join("");
}

function render(data){
  walletState=data;
  const locked=document.getElementById("wa-locked");
  const enabled=document.getElementById("wa-enabled");
  const feeUSD="$"+((data.wallet_fee_cents||0)/100).toFixed(2)+" USD";
  setText("wa-fee-header",feeUSD); setText("wa-fee-header2",feeUSD);
  if(data.wallet_enabled){ if(locked) locked.hidden=true; if(enabled) enabled.hidden=false; renderMethods(data.wallet_methods||[]); }
  else { if(locked) locked.hidden=false; if(enabled) enabled.hidden=true; }
  renderActivations(data.wallet_activations||[]);
  setText("wd-available", U.formatUSD(data.summary.dollar_balance_cents||0));
  setText("wd-coins", U.formatNumber(data.summary.balance||0));
  setText("wd-wallet-status", data.wallet_active?"Active":"Inactive");
  setText("wd-min", U.formatUSD(data.min_withdrawal_cents||0));
  const sel=document.getElementById("wd-method");
  if(sel){
    const ms=data.withdrawal_methods||[]; sel.innerHTML="";
    if(!ms.length){ const o=document.createElement("option"); o.value=""; o.textContent="No methods enabled"; sel.appendChild(o); sel.disabled=true; }
    else { sel.disabled=false; ms.forEach(m=>{ const o=document.createElement("option"); o.value=m.code; o.textContent=m.label; sel.appendChild(o); }); }
  }
  renderWithdrawals(data.withdrawals||[]);
  startWithdrawTimer(data.withdrawal_open===true, data.withdrawal_target_ms, data.withdrawal_timer_enabled);
  const wdB=document.getElementById("wd-submit");
  if(wdB) wdB.disabled = !data.withdrawal_open || !data.wallet_active || !(data.withdrawal_methods||[]).length;
}

function startWithdrawTimer(isOpen, targetMs, enabled){
  const state=document.getElementById("wd-window-state");
  const note=document.getElementById("wd-timer-note");
  if(withdrawTimerId){ clearInterval(withdrawTimerId); withdrawTimerId=null; }
  if(!enabled){ if(state){ state.textContent="Disabled"; state.className="pill pill-muted"; } if(note) note.textContent="Withdrawals disabled by the administrator."; setTimerDisplay(0); return; }
  if(isOpen){ if(state){ state.textContent="OPEN"; state.className="pill pill-green"; } if(note) note.textContent="Withdrawals open. Submit below."; setTimerDisplay(0); return; }
  if(state){ state.textContent="CLOSED"; state.className="pill pill-amber"; }
  if(note) note.textContent="Withdrawals open when the timer ends.";
  const tick=()=>{ const ms=Math.max(0, (targetMs||0) - Date.now()); setTimerDisplay(ms); if(ms<=0 && withdrawTimerId){ clearInterval(withdrawTimerId); withdrawTimerId=null; if(window.Fox.wallet) window.Fox.wallet.load(true); } };
  tick(); withdrawTimerId=setInterval(tick,1000);
}

function setTimerDisplay(ms){
  const totalSec=Math.floor(ms/1000);
  const d=Math.floor(totalSec/86400);
  const h=Math.floor((totalSec%86400)/3600);
  const m=Math.floor((totalSec%3600)/60);
  const s=totalSec%60;
  const pad=(n)=>String(n).padStart(2,"0");
  const setN=(id,v)=>{ const el=document.getElementById(id); if(el) el.textContent=v; };
  setN("tm-days", pad(d)); setN("tm-hours", pad(h)); setN("tm-minutes", pad(m)); setN("tm-seconds", pad(s));
}

function initWithdrawSubmit(){
  const btn=document.getElementById("wd-submit");
  if(!btn || btn.dataset.bound==="1") return; btn.dataset.bound="1";
  btn.addEventListener("click", async ()=>{
    showError("wd-error","");
    if(!window.Fox.state.authenticated){ U.toast("Open inside Telegram.","info"); return; }
    if(!walletState) return;
    const method=document.getElementById("wd-method").value;
    const amountStr=document.getElementById("wd-amount").value;
    const dest=document.getElementById("wd-destination").value.trim();
    const amount=parseFloat(amountStr);
    if(!method){ showError("wd-error","Choose a method."); return; }
    if(!isFinite(amount)||amount<=0){ showError("wd-error","Enter a valid amount."); return; }
    if(!dest){ showError("wd-error","Enter destination."); return; }
    const cents=Math.round(amount*100);
    if(!window.confirm("Submit withdrawal of $"+amount.toFixed(2)+"?")) return;
    U.setLoading(btn,true,"Submitting…");
    try{
      await API.post("/api/withdrawals",{amount_cents:cents, method, destination:dest, idempotency_key:"wd_"+Date.now().toString(36)+"_"+Math.random().toString(36).slice(2,8)});
      U.toast("Withdrawal submitted.","success"); TG.hapticNotify("success");
      document.getElementById("wd-amount").value=""; document.getElementById("wd-destination").value="";
      await load(true);
    } catch(err){ showError("wd-error",err.message||"Failed."); }
    finally { U.setLoading(btn,false); }
  });
}

function bindAll(){
  initTabs(); initScreenshot(); initWithdrawSubmit();
  const waSub=document.getElementById("wa-submit");
  if(waSub && waSub.dataset.bound!=="1"){ waSub.dataset.bound="1"; waSub.addEventListener("click",submitActivation); }
  const waCan=document.getElementById("wa-cancel");
  if(waCan && waCan.dataset.bound!=="1"){ waCan.dataset.bound="1"; waCan.addEventListener("click",()=>{ activeActivation=null; resetScreenshot(); const f=document.getElementById("wa-form-wrap"); if(f) f.hidden=true; document.querySelectorAll("#wa-methods .pay-card").forEach(p=>p.classList.remove("is-selected")); }); }
}

async function load(force){
  if(loaded && !force) return;
  if(!window.Fox.state.authenticated){ renderPreview(); loaded=true; return; }
  try{ const d=await API.get("/api/wallet"); render(d); loaded=true; }
  catch(err){ const e=document.getElementById("wd-eligibility"); if(e) e.textContent=err.message||"Could not load wallet."; }
}

window.Fox=window.Fox||{}; window.Fox.screenHooks=window.Fox.screenHooks||{};
window.Fox.screenHooks.wallet=()=>{ bindAll(); load(false); };
window.Fox.wallet={ load, bindAll };
})();
'''

FILES["frontend/assets/js/profile.js"] = r'''(function(){
"use strict";
const U=window.Fox.ui, API=window.Fox.api, TG=window.Fox.tg;
let txOffset=0; const TX_LIMIT=20; let txLoading=false, txExhausted=false;

function setText(id,v){ const n=document.getElementById(id); if(n) n.textContent=v; }

function renderPreview(){
  setText("profile-name","—");
  setText("profile-username","Open inside Telegram to sign in");
  setText("profile-id","—");
  setText("profile-coins","0"); setText("profile-dollars","$0.00"); setText("profile-refs","0");
  setText("profile-wallet-status","—");
  const box=document.getElementById("profile-avatar"); if(box) box.innerHTML='<span id="profile-avatar-fallback">•</span>';
  const tx=document.getElementById("tx-list"); if(tx) tx.innerHTML='<li class="empty-state">Open inside Telegram.</li>';
}

function renderProfile(data){
  const u=data.user||{}, s=data.stats||{};
  setText("profile-name", u.display_name||"—");
  setText("profile-username", u.username?"@"+u.username:"No username");
  setText("profile-id", "Telegram ID: "+(u.telegram_id ? String(u.telegram_id) : "—"));
  setText("profile-coins", U.formatNumber(s.balance||0));
  setText("profile-dollars", U.formatUSD(s.dollar_balance_cents||0));
  setText("profile-refs", U.formatNumber(s.valid_referrals||0));
  setText("profile-wallet-status", data.wallet_active ? "Active ✓" : "Inactive");
  const box=document.getElementById("profile-avatar");
  if(box){
    const photo=u.photo_url||TG.getPhotoUrl();
    if(photo) box.innerHTML='<img src="'+U.escapeHtml(photo)+'" alt="" referrerpolicy="no-referrer"/>';
    else { const init=(u.display_name||TG.getDisplayName()||"•").trim().charAt(0).toUpperCase(); box.innerHTML='<span id="profile-avatar-fallback">'+U.escapeHtml(init)+"</span>"; }
  }
}

function renderTx(rows,append){
  const host=document.getElementById("tx-list"); if(!host) return;
  if(!append && (!rows || !rows.length)){ host.innerHTML='<li class="empty-state">No transactions yet.</li>'; return; }
  const html=rows.map(t=>{
    const pos=Number(t.amount)>=0; const sg=pos?"+":"−";
    const unit = t.unit==="usd_cents" ? U.formatUSD(Math.abs(Number(t.amount))) : U.formatNumber(Math.abs(Number(t.amount)));
    return '<li><span class="tx-main"><span class="tx-title">'+U.escapeHtml(t.label||t.type)+'</span>'+
      '<span class="tx-sub">'+U.escapeHtml(U.formatDateTime(t.created_at))+'</span></span>'+
      '<span class="tx-amount '+(pos?"plus":"minus")+'">'+sg+unit+'</span></li>';
  }).join("");
  if(append) host.insertAdjacentHTML("beforeend",html); else host.innerHTML=html;
}

async function loadTransactions(reset){
  if(txLoading) return;
  if(!window.Fox.state.authenticated){ renderPreview(); return; }
  if(reset){ txOffset=0; txExhausted=false; txLoading=false; }
  if(txExhausted) return;
  txLoading=true;
  const moreBtn=document.getElementById("tx-more-btn"); if(moreBtn) moreBtn.disabled=true;
  try{
    const res=await API.get("/api/transactions?limit="+TX_LIMIT+"&offset="+txOffset);
    const rows=res.transactions||[];
    renderTx(rows, txOffset>0);
    txOffset+=rows.length;
    txExhausted=rows.length<TX_LIMIT;
    if(moreBtn) moreBtn.hidden=txExhausted;
  } catch(err){ const host=document.getElementById("tx-list"); if(host && txOffset===0) host.innerHTML='<li class="empty-state">'+U.escapeHtml(err.message||"Could not load.")+"</li>"; }
  finally { txLoading=false; if(moreBtn) moreBtn.disabled=false; }
}

function initButtons(){
  const b=document.getElementById("tx-more-btn");
  if(b && b.dataset.bound!=="1"){ b.dataset.bound="1"; b.addEventListener("click",()=>loadTransactions(false)); }
  const w=document.getElementById("open-wallet-btn");
  if(w && w.dataset.bound!=="1"){ w.dataset.bound="1"; w.addEventListener("click",()=>{ U.showScreen("wallet"); }); }
}

async function load(){
  if(!window.Fox.state.authenticated){ renderPreview(); return; }
  try{ const d=await API.get("/api/profile"); renderProfile(d); }
  catch(err){ if(err && err.status===401) return; }
}

window.Fox=window.Fox||{}; window.Fox.screenHooks=window.Fox.screenHooks||{};
window.Fox.screenHooks.profile=()=>{ initButtons(); load(); };
window.Fox.screenHooks.transactions=()=>loadTransactions(true);
window.Fox.profile={ load, initTransactionsButton:initButtons, loadTransactions };
})();
'''

FILES["frontend/assets/js/app.js"] = r'''(function(){
"use strict";
const CFG=window.FOX_CONFIG, U=window.Fox.ui, API=window.Fox.api, TG=window.Fox.tg;
window.Fox.state={ ready:false, authenticated:false, profile:null };

function sleep(ms){ return new Promise(r=>setTimeout(r,ms)); }

function setPreview(reason){
  window.Fox.state.authenticated=false;
  API.clearToken();
  U.showBanner(reason||"Open inside Telegram to sign in.","offline");
}

async function authenticate(){
  if(!TG.isInsideTelegram()){ setPreview("Preview mode — open inside Telegram."); return false; }
  try{
    const res=await API.authenticate(TG.state.initData);
    if(res && res.token){ API.setToken(res.token); window.Fox.state.authenticated=true; U.hideBanner(); return true; }
    throw new Error("No token.");
  } catch(err){
    if(err && (err.code==="network_error" || err.code==="timeout")){
      U.showBanner("Backend unreachable. Retrying…","offline");
      await sleep(2000);
      try{ const r2=await API.authenticate(TG.state.initData); if(r2 && r2.token){ API.setToken(r2.token); window.Fox.state.authenticated=true; U.hideBanner(); return true; } }catch(e){}
      setPreview("Cannot reach server. Preview mode."); return false;
    }
    if(err && err.code==="maintenance_mode"){ setPreview("Maintenance mode."); return false; }
    setPreview("Sign-in failed: "+(err.message||"unknown")); return false;
  }
}

function bindNavigation(){
  document.querySelectorAll("[data-nav]").forEach(b=>b.addEventListener("click",()=>{ U.showScreen(b.getAttribute("data-nav")); TG.hapticImpact("light"); }));
  document.querySelectorAll("[data-goto]").forEach(b=>b.addEventListener("click",()=>{ U.showScreen(b.getAttribute("data-goto")); TG.hapticImpact("light"); }));
  if(U.el.backBtn) U.el.backBtn.addEventListener("click",()=>{ U.goBack(); TG.hapticImpact("light"); });
  if(U.el.refreshBtn) U.el.refreshBtn.addEventListener("click", async ()=>{ U.setLoading(U.el.refreshBtn,true,""); await refreshAll(true); U.setLoading(U.el.refreshBtn,false); U.toast("Refreshed.","success"); });
  const rb=document.getElementById("reload-app-btn"); if(rb) rb.addEventListener("click",()=>window.location.reload());
}

async function refreshAll(force){
  await Promise.all([
    window.Fox.home     ? window.Fox.home.load()      : null,
    window.Fox.tasks    ? window.Fox.tasks.load()     : null,
    window.Fox.referrals? window.Fox.referrals.load(force) : null,
    window.Fox.wallet   ? window.Fox.wallet.load(force) : null,
    window.Fox.profile  ? window.Fox.profile.load()   : null
  ]);
}

function startHealthMonitor(){
  if(!API.isConfigured()) return;
  if(!window.Fox.state.authenticated) return;
  let wasDown=false;
  async function check(){
    try{ await API.health(); if(wasDown){ U.toast("Backend reachable again.","success"); wasDown=false; refreshAll(true); } }
    catch(err){ if(!wasDown){ wasDown=true; U.showBanner("Backend unavailable.","offline"); } }
  }
  setInterval(check, CFG.HEALTH_RETRY_MS); check();
}

async function boot(){
  U.init();
  window.addEventListener("unhandledrejection",ev=>console.error("[FOX]",ev.reason));
  API.setUnauthorizedHandler(()=>U.showBanner("Session expired.","offline"));
  TG.init();
  if(window.Fox.home) window.Fox.home.initTapButton();
  bindNavigation();

  if(API.isConfigured()) await authenticate();
  else setPreview("Backend URL not configured.");

  await refreshAll(true);
  U.showScreen("home");
  startHealthMonitor();
  U.hideBootLoader();
  window.Fox.state.ready=true;
}
if(document.readyState==="loading") document.addEventListener("DOMContentLoaded",boot);
else boot();
})();
'''

FILES["frontend/assets/css/style.css"] = r''':root{
--navy-900:#050a14;--navy-800:#070d1b;--navy-700:#0c1426;--navy-600:#121d33;--line:#1e2c4a;
--cyan:#22d3ee;--cyan-soft:#67e8f9;--cyan-glow:rgba(34,211,238,.35);
--orange:#ff8a3d;--gold:#ffd166;--gold-deep:#f2a93b;
--green:#34d399;--red:#f87171;--amber:#fbbf24;
--text:#fff;--text-muted:#93a4c4;--text-dim:#66799c;
--radius:16px;--shadow-card:0 10px 30px rgba(0,0,0,.45);
--nav-h:64px;--header-h:58px;
--safe-top:env(safe-area-inset-top,0px);--safe-bottom:env(safe-area-inset-bottom,0px);
--font:"Manrope",-apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,Arial,sans-serif}
*,*::before,*::after{box-sizing:border-box}
html,body{margin:0;padding:0;height:100%;overflow-x:hidden}
body{font-family:var(--font);background:var(--navy-800);color:var(--text);font-size:15px;line-height:1.45;-webkit-font-smoothing:antialiased;-webkit-tap-highlight-color:transparent;max-width:100vw}
body::before{content:"";position:fixed;inset:0;pointer-events:none;z-index:0;background:radial-gradient(60% 42% at 12% 0%,rgba(34,211,238,.16),transparent 60%),radial-gradient(55% 40% at 92% 6%,rgba(255,138,61,.13),transparent 62%),radial-gradient(80% 50% at 50% 108%,rgba(34,211,238,.10),transparent 70%)}
button,input,select{font:inherit;color:inherit}
button{cursor:pointer;border:none;background:none}
ul{list-style:none;margin:0;padding:0}
h1,h2,h3,p{margin:0}
img,svg{display:block;max-width:100%}
:focus-visible{outline:2px solid var(--cyan);outline-offset:2px;border-radius:6px}
.app{position:relative;z-index:1;min-height:100dvh;display:flex;flex-direction:column;max-width:560px;margin:0 auto;width:100%}
.app-header{position:sticky;top:0;z-index:30;display:flex;align-items:center;justify-content:space-between;gap:10px;padding:calc(var(--safe-top) + 10px) 14px 10px;min-height:calc(var(--header-h) + var(--safe-top));background:linear-gradient(180deg,rgba(7,13,27,.97),rgba(7,13,27,.82));backdrop-filter:blur(14px);border-bottom:1px solid rgba(34,211,238,.10)}
.brand{display:flex;align-items:center;gap:9px;min-width:0}
.brand-fox{width:30px;height:30px;flex:0 0 auto;filter:drop-shadow(0 0 8px rgba(255,138,61,.45))}
.brand-name{font-weight:800;font-size:17px;letter-spacing:1.2px;white-space:nowrap}
.brand-name-accent{color:var(--cyan);text-shadow:0 0 14px var(--cyan-glow);margin-left:3px}
.icon-btn{width:38px;height:38px;display:grid;place-items:center;border-radius:12px;color:var(--text-muted);background:rgba(255,255,255,.04);border:1px solid rgba(255,255,255,.06);flex:0 0 auto}
.icon-btn svg{width:20px;height:20px}
.icon-btn:hover{color:var(--cyan);background:rgba(34,211,238,.10)}
.view{flex:1 1 auto;padding:14px 14px calc(var(--nav-h) + var(--safe-bottom) + 22px);min-width:0}
.screen{animation:fade-in .26s ease both}
.screen[hidden]{display:none!important}
@keyframes fade-in{from{opacity:0;transform:translateY(8px)}to{opacity:1;transform:none}}
.screen-title{font-size:22px;font-weight:800}
.screen-sub{color:var(--text-muted);font-size:13px;margin-top:5px;margin-bottom:14px}
.status-banner{position:fixed;top:calc(var(--safe-top) + 8px);left:50%;transform:translateX(-50%);z-index:60;max-width:calc(100vw - 28px);padding:9px 16px;border-radius:999px;font-size:12.5px;font-weight:700;text-align:center;backdrop-filter:blur(12px);box-shadow:0 6px 22px rgba(0,0,0,.5)}
.status-banner[data-kind="offline"]{background:rgba(248,113,113,.16);border:1px solid rgba(248,113,113,.45);color:#fecaca}
.status-banner[data-kind="ok"]{background:rgba(52,211,153,.14);border:1px solid rgba(52,211,153,.4);color:#a7f3d0}
.card{background:linear-gradient(160deg,rgba(18,29,51,.92),rgba(12,20,38,.92));border:1px solid #1e2c4a;border-radius:var(--radius);padding:15px;margin-bottom:13px;box-shadow:var(--shadow-card);position:relative;overflow:hidden;min-width:0}
.card::after{content:"";position:absolute;inset:0 0 auto 0;height:1px;background:linear-gradient(90deg,transparent,rgba(34,211,238,.35),transparent)}
.card-title{font-size:14px;font-weight:700}
.card-hint{color:var(--text-dim);font-size:12px}
.row-between{display:flex;align-items:center;justify-content:space-between;gap:10px}
.mt-4{margin-top:4px}.mt-8{margin-top:8px}.mt-12{margin-top:12px}
.stack>*+*{margin-top:12px}
.profile-card{display:flex;align-items:center;gap:13px}
.avatar{width:52px;height:52px;border-radius:50%;flex:0 0 auto;display:grid;place-items:center;font-weight:800;font-size:20px;color:var(--navy-900);background:linear-gradient(135deg,var(--cyan),var(--orange));box-shadow:0 0 0 2px rgba(34,211,238,.22);overflow:hidden}
.avatar-lg{width:68px;height:68px;font-size:26px}
.avatar img{width:100%;height:100%;object-fit:cover}
.profile-meta{min-width:0;flex:1 1 auto}
.profile-hello{color:var(--text-dim);font-size:11.5px;text-transform:uppercase;letter-spacing:.9px}
.profile-name{font-size:17px;font-weight:800;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
.profile-sub{color:var(--text-muted);font-size:12.5px;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
.dual-balance{display:grid;grid-template-columns:1fr 1fr;gap:11px;margin-bottom:13px}
.dual-balance .card{margin-bottom:0}
.balance-card{background:radial-gradient(120% 90% at 100% 0%,rgba(255,209,102,.16),transparent 55%),linear-gradient(160deg,rgba(18,29,51,.95),rgba(12,20,38,.95));border-color:rgba(255,209,102,.22)}
.dollar-card{background:radial-gradient(120% 90% at 100% 0%,rgba(52,211,153,.14),transparent 55%),linear-gradient(160deg,rgba(18,29,51,.95),rgba(12,20,38,.95));border-color:rgba(52,211,153,.22)}
.balance-label{color:var(--text-muted);font-size:11.5px}
.balance-value{display:flex;align-items:center;gap:7px;font-size:22px;font-weight:800;color:var(--gold);text-shadow:0 0 16px rgba(255,209,102,.3);margin-top:2px;word-break:break-all}
.dollar-value{color:var(--green);text-shadow:0 0 16px rgba(52,211,153,.3)}
.balance-sub{color:var(--text-dim);font-size:10.5px;margin-top:4px}
.coin-dot{width:14px;height:14px;border-radius:50%;background:radial-gradient(circle at 32% 30%,#fff2c4,var(--gold) 42%,var(--gold-deep));box-shadow:0 0 10px rgba(255,209,102,.55);flex:0 0 auto}
.balance-split{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:8px;margin-top:13px;padding-top:12px;border-top:1px dashed rgba(255,255,255,.09)}
.mini-label{color:var(--text-dim);font-size:10.5px;text-transform:uppercase;letter-spacing:.7px}
.mini-value{font-size:14px;font-weight:700;margin-top:2px;word-break:break-all}
.tap-zone{display:grid;place-items:center;padding:16px 0 20px;position:relative}
.tap-button{position:relative;width:min(62vw,232px);height:min(62vw,232px);border-radius:50%;display:grid;place-items:center;background:radial-gradient(circle at 50% 38%,rgba(34,211,238,.28),transparent 62%),linear-gradient(160deg,var(--navy-600),var(--navy-800));border:2px solid rgba(34,211,238,.42);box-shadow:0 0 0 8px rgba(34,211,238,.06),0 0 36px rgba(34,211,238,.25);user-select:none;touch-action:manipulation;-webkit-user-select:none}
.tap-button:active,.tap-button.is-tapped{transform:scale(.955)}
.tap-button:disabled{opacity:.45;filter:grayscale(.5)}
.tap-ring{position:absolute;inset:-14px;border-radius:50%;border:1px dashed rgba(34,211,238,.30);animation:spin 14s linear infinite;pointer-events:none}
@keyframes spin{to{transform:rotate(360deg)}}
.tap-fox{width:46%;height:46%;filter:drop-shadow(0 6px 16px rgba(255,138,61,.4))}
.tap-caption{position:absolute;bottom:17%;font-size:11.5px;font-weight:800;letter-spacing:2px;color:var(--cyan-soft);text-shadow:0 0 12px var(--cyan-glow)}
.tap-floaters{position:absolute;inset:0;pointer-events:none;overflow:visible}
.floater{position:absolute;font-weight:800;font-size:19px;color:var(--gold);text-shadow:0 0 14px rgba(255,209,102,.7);animation:float-up .95s ease-out forwards;pointer-events:none}
@keyframes float-up{0%{opacity:0;transform:translate(-50%,0) scale(.7)}22%{opacity:1;transform:translate(-50%,-22px) scale(1.12)}100%{opacity:0;transform:translate(-50%,-92px) scale(.92)}}
.leader-list>li{display:flex;align-items:center;gap:10px;padding:10px 0;border-bottom:1px solid rgba(255,255,255,.05);min-width:0}
.leader-list>li:last-child{border-bottom:none}
.li-main{flex:1 1 auto;min-width:0}
.li-name{font-size:14px;font-weight:700;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
.li-sub{font-size:11.5px;color:var(--text-dim);white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
.empty-state{color:var(--text-dim);font-size:13px;text-align:center;padding:18px 6px;border-bottom:none!important;display:block!important}
.pill{display:inline-flex;align-items:center;gap:4px;padding:3px 9px;border-radius:999px;font-size:10.5px;font-weight:800;letter-spacing:.5px;text-transform:uppercase;white-space:nowrap}
.pill-cyan{background:rgba(34,211,238,.13);color:var(--cyan-soft);border:1px solid rgba(34,211,238,.32)}
.pill-amber{background:rgba(251,191,36,.13);color:var(--amber);border:1px solid rgba(251,191,36,.32)}
.pill-green{background:rgba(52,211,153,.13);color:var(--green);border:1px solid rgba(52,211,153,.32)}
.pill-red{background:rgba(248,113,113,.13);color:var(--red);border:1px solid rgba(248,113,113,.32)}
.pill-muted{background:rgba(255,255,255,.06);color:var(--text-dim);border:1px solid rgba(255,255,255,.08)}
.btn{display:inline-flex;align-items:center;justify-content:center;gap:7px;width:100%;padding:13px 16px;border-radius:14px;font-weight:800;font-size:14px;min-height:46px}
.btn:active{transform:scale(.975)}
.btn:disabled{opacity:.5;cursor:not-allowed;transform:none}
.btn-primary{background:linear-gradient(135deg,var(--cyan),#0ea5b7);color:#04222a;box-shadow:0 8px 24px rgba(34,211,238,.28)}
.btn-ghost{background:rgba(255,255,255,.045);border:1px solid #1e2c4a;color:var(--text-muted)}
.btn-compact{width:auto;padding:11px 16px;min-height:42px;flex:0 0 auto}
.list-btn{display:flex;width:100%;align-items:center;justify-content:space-between;padding:12px 10px;border-radius:12px;font-size:14px;font-weight:600;color:var(--text);text-align:left}
.field-label{display:block;font-size:11.5px;text-transform:uppercase;letter-spacing:.8px;color:var(--text-dim);margin-bottom:6px;font-weight:700}
.text-input{width:100%;padding:12px 13px;border-radius:13px;background:rgba(5,10,20,.75);border:1px solid #1e2c4a;color:var(--text);font-size:14px;min-width:0}
.text-input::placeholder{color:var(--text-dim)}
.text-input:focus{outline:none;border-color:rgba(34,211,238,.55);box-shadow:0 0 0 3px rgba(34,211,238,.12)}
select.text-input{appearance:none}
.copy-row{display:flex;gap:8px;align-items:stretch;margin-top:9px}
.copy-row .text-input{flex:1 1 auto}
.form-error{margin-top:10px;padding:10px 12px;border-radius:11px;background:rgba(248,113,113,.12);border:1px solid rgba(248,113,113,.34);color:#fecaca;font-size:12.5px}
.kv-list li{display:flex;align-items:center;justify-content:space-between;gap:12px;padding:10px 0;border-bottom:1px solid rgba(255,255,255,.05);font-size:13.5px}
.kv-list li:last-child{border-bottom:none}
.kv-list span{color:var(--text-muted)}
.kv-list b{font-weight:700;text-align:right}
.tx-list>li{display:flex;align-items:center;gap:11px;padding:12px 13px;margin-bottom:9px;border-radius:var(--radius);background:linear-gradient(160deg,rgba(18,29,51,.9),rgba(12,20,38,.9));border:1px solid #1e2c4a}
.tx-main{flex:1 1 auto;min-width:0}
.tx-title{font-size:13.5px;font-weight:700;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
.tx-sub{font-size:11px;color:var(--text-dim)}
.tx-amount{font-weight:800;font-size:14px;flex:0 0 auto}
.tx-amount.plus{color:var(--green)}.tx-amount.minus{color:var(--red)}
.bottom-nav{position:fixed;left:50%;transform:translateX(-50%);bottom:0;width:100%;max-width:560px;z-index:40;display:grid;padding:7px 6px calc(var(--safe-bottom) + 7px);background:linear-gradient(180deg,rgba(7,13,27,.86),rgba(5,10,20,.985));backdrop-filter:blur(16px);border-top:1px solid rgba(34,211,238,.12)}
.bottom-nav.nav-4{grid-template-columns:repeat(4,1fr)}
.nav-btn{display:flex;flex-direction:column;align-items:center;gap:3px;padding:6px 2px;border-radius:12px;color:var(--text-dim);font-size:10px;font-weight:700;min-width:0}
.nav-btn svg{width:21px;height:21px}
.nav-btn.is-active{color:var(--cyan);background:rgba(34,211,238,.09)}
.nav-btn.is-active svg{filter:drop-shadow(0 0 8px var(--cyan-glow))}
.toast-host{position:fixed;left:50%;transform:translateX(-50%);bottom:calc(var(--nav-h) + var(--safe-bottom) + 16px);z-index:90;display:flex;flex-direction:column;gap:8px;align-items:center;width:min(92vw,420px);pointer-events:none}
.toast{width:100%;padding:11px 15px;border-radius:13px;font-size:13px;font-weight:600;text-align:center;backdrop-filter:blur(12px);box-shadow:0 10px 30px rgba(0,0,0,.5);animation:toast-in .24s ease both;word-break:break-word}
.toast.out{animation:toast-out .24s ease both}
@keyframes toast-in{from{opacity:0;transform:translateY(14px)}to{opacity:1;transform:none}}
@keyframes toast-out{from{opacity:1}to{opacity:0;transform:translateY(10px)}}
.toast-success{background:rgba(52,211,153,.16);border:1px solid rgba(52,211,153,.45);color:#a7f3d0}
.toast-error{background:rgba(248,113,113,.16);border:1px solid rgba(248,113,113,.45);color:#fecaca}
.toast-info{background:rgba(34,211,238,.14);border:1px solid rgba(34,211,238,.4);color:#a5f3fc}
.boot-loader{position:fixed;inset:0;z-index:200;display:grid;place-content:center;justify-items:center;gap:18px;background:var(--navy-800);transition:opacity .35s,visibility .35s}
.boot-loader.is-hidden{opacity:0;visibility:hidden;pointer-events:none}
.boot-fox{width:96px;height:96px;animation:bob 1.7s ease-in-out infinite;filter:drop-shadow(0 0 22px rgba(255,138,61,.4))}
@keyframes bob{0%,100%{transform:translateY(0) scale(1)}50%{transform:translateY(-11px) scale(1.05)}}
.boot-text{color:var(--text-muted);font-size:13px;font-weight:600;letter-spacing:.6px}
.skeleton-card{height:92px;border-radius:var(--radius);border:1px solid #1e2c4a;background:linear-gradient(100deg,rgba(18,29,51,.85) 30%,rgba(34,211,238,.09) 50%,rgba(18,29,51,.85) 70%);background-size:220% 100%;animation:shimmer 1.4s linear infinite}
@keyframes shimmer{from{background-position:180% 0}to{background-position:-80% 0}}
.disclaimer{color:var(--text-dim);font-size:11.5px;line-height:1.55;text-align:center;padding:8px 10px 4px}
.tabs{display:grid;grid-auto-flow:column;grid-auto-columns:1fr;gap:6px;padding:5px;border-radius:14px;background:rgba(5,10,20,.6);border:1px solid #1e2c4a;margin-bottom:13px}
.tab{padding:10px 6px;border-radius:10px;font-size:12.5px;font-weight:800;letter-spacing:.3px;color:var(--text-dim)}
.tab.is-active{color:var(--navy-900);background:linear-gradient(135deg,var(--cyan),#0ea5b7);box-shadow:0 4px 14px rgba(34,211,238,.3)}
.tab-panel[hidden]{display:none!important}
.upload-zone{position:relative;display:flex;flex-direction:column;align-items:center;justify-content:center;gap:6px;padding:18px 14px;border:2px dashed #1e2c4a;border-radius:14px;background:rgba(5,10,20,.55);cursor:pointer;text-align:center;margin-top:6px}
.upload-zone.has-file{border-style:solid;border-color:rgba(52,211,153,.6);background:rgba(52,211,153,.06)}
.upload-zone input[type="file"]{display:none}
.upload-icon{font-size:22px;line-height:1}
.upload-text{font-size:13px;font-weight:700;color:var(--text)}
.upload-hint{font-size:11px;color:var(--text-dim)}
.upload-preview{position:relative;margin-top:10px;border-radius:12px;overflow:hidden;border:1px solid #1e2c4a;background:#000}
.upload-preview img{width:100%;height:auto;max-height:260px;object-fit:contain;display:block}
.upload-remove{position:absolute;top:8px;right:8px;width:30px;height:30px;border-radius:50%;background:rgba(0,0,0,.75);color:#fff;font-weight:800;font-size:14px;display:grid;place-items:center;border:1px solid rgba(255,255,255,.2)}
.ref-count-badge{font-size:16px;font-weight:800;color:var(--cyan);text-shadow:0 0 12px var(--cyan-glow)}
.milestone-claim-list>li{display:flex;align-items:center;justify-content:space-between;gap:10px;padding:12px 0;border-bottom:1px solid rgba(255,255,255,.06)}
.milestone-claim-list>li:last-child{border-bottom:none}
.ms-left{display:flex;flex-direction:column;gap:2px;min-width:0}
.ms-title{font-size:13.5px;font-weight:700}
.ms-reward{font-size:14px;font-weight:800;color:var(--green)}
.ms-status{font-size:11px;color:var(--text-dim);margin-top:2px}
.ms-btn{min-width:96px}
.pay-methods{display:grid;grid-template-columns:1fr;gap:11px;margin-bottom:13px}
.pay-card{display:flex;align-items:center;gap:12px;padding:14px;border-radius:var(--radius);background:linear-gradient(160deg,rgba(18,29,51,.9),rgba(12,20,38,.9));border:1px solid #1e2c4a;cursor:pointer;text-align:left}
.pay-card.is-selected{border-color:rgba(34,211,238,.65);box-shadow:0 0 0 2px rgba(34,211,238,.15)}
.pay-logo{width:40px;height:40px;flex:0 0 auto;border-radius:11px;display:grid;place-items:center;font-weight:800;font-size:15px;color:#fff}
.pay-logo.okx{background:#000}
.pay-logo.bybit{background:#f7a600}
.pay-logo.binance{background:#f0b90b;color:#000}
.pay-info{flex:1 1 auto;min-width:0}
.pay-name{font-size:14px;font-weight:800}
.pay-fee{font-size:12px;color:var(--text-dim);margin-top:2px}
.pay-arrow{color:var(--text-dim);font-size:16px}
.lock-banner{display:flex;align-items:center;gap:13px}
.lock-icon{font-size:30px;line-height:1;flex:0 0 auto}
.deposit-instructions{padding:12px;border-radius:12px;background:rgba(34,211,238,.06);border:1px solid rgba(34,211,238,.25);font-size:13px;line-height:1.5;white-space:pre-wrap;word-break:break-word;margin-top:8px}
.deposit-instructions code{background:rgba(0,0,0,.4);padding:2px 6px;border-radius:5px;font-family:ui-monospace,monospace;font-size:12px;color:var(--cyan-soft);word-break:break-all}
.timer-grid{display:grid;grid-template-columns:repeat(4, minmax(0, 1fr));gap:8px;margin-top:12px;width:100%}
.timer-cell{display:flex;flex-direction:column;align-items:center;justify-content:center;gap:4px;padding:10px 4px 8px;background:rgba(5,10,20,.75);border:1px solid #1e2c4a;border-radius:12px;min-width:0;overflow:hidden}
.timer-num{font-family:"Courier New", ui-monospace, monospace;font-size:clamp(16px, 5.5vw, 24px);font-weight:800;color:var(--cyan);text-shadow:0 0 12px var(--cyan-glow);letter-spacing:.5px;line-height:1;white-space:nowrap}
.timer-label{font-size:10px;font-weight:700;color:var(--text-dim);text-transform:uppercase;letter-spacing:.5px;line-height:1;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;max-width:100%}
@media (max-width:340px){.timer-num{font-size:14px}.timer-label{font-size:9px;letter-spacing:.3px}.timer-grid{gap:4px}.timer-cell{padding:8px 2px 6px}}
@media (prefers-reduced-motion:reduce){*,*::before,*::after{animation-duration:.001ms!important;transition-duration:.001ms!important}}
'''

FILES["frontend/admin/index.html"] = r'''<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8"/>
<meta name="viewport" content="width=device-width,initial-scale=1,maximum-scale=1,user-scalable=no,viewport-fit=cover"/>
<meta name="theme-color" content="#070d1b"/>
<title>FOX EARN — Admin</title>
<link rel="preconnect" href="https://fonts.googleapis.com"/>
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin/>
<link href="https://fonts.googleapis.com/css2?family=Manrope:wght@400;500;600;700;800&display=swap" rel="stylesheet"/>
<link rel="stylesheet" href="/assets/css/style.css"/>
<script src="https://telegram.org/js/telegram-web-app.js"></script>
</head>
<body>
<div id="status-banner" class="status-banner" hidden><span id="status-banner-text"></span></div>
<div id="app" class="app">
<header class="app-header">
  <div class="brand">
    <svg class="brand-fox" viewBox="0 0 200 200" aria-hidden="true">
      <polygon points="40,72 28,14 86,50" fill="#ff8a3d"/><polygon points="160,72 172,14 114,50" fill="#ff8a3d"/>
      <path d="M100 40 L166 76 L150 136 L100 172 L50 136 L34 76 Z" fill="#ff8a3d"/>
      <path d="M100 106 L136 131 L100 168 L64 131 Z" fill="#fff3e6"/>
      <circle cx="72" cy="101" r="8.5" fill="#0b1220"/><circle cx="128" cy="101" r="8.5" fill="#0b1220"/>
    </svg>
    <span class="brand-name">FOX<span class="brand-name-accent">ADMIN</span></span>
  </div>
</header>
<main id="view" class="view">
  <div id="admin-auth-error" class="card" hidden>
    <p class="card-title">Access denied</p>
    <p class="card-hint mt-8" id="admin-auth-error-msg">Only authorized administrators may use this panel.</p>
  </div>
  <div id="admin-app" hidden>
    <h2 class="screen-title">Admin</h2>
    <div class="tabs">
      <button class="tab is-active" data-atab="stats" type="button">Stats</button>
      <button class="tab" data-atab="activations" type="button">Wallet</button>
      <button class="tab" data-atab="withdrawals" type="button">Withdrawals</button>
      <button class="tab" data-atab="settings" type="button">Settings</button>
    </div>
    <div class="tab-panel" data-apanel="stats">
      <div class="card"><p class="card-title">Statistics</p><ul class="kv-list" id="admin-stats"></ul></div>
      <div class="card"><p class="card-title">Audit log</p><ul class="leader-list" id="admin-audit"><li class="empty-state">None.</li></ul></div>
    </div>
    <div class="tab-panel" data-apanel="activations" hidden>
      <div class="card">
        <div class="row-between">
          <p class="card-title">Activations</p>
          <select id="admin-wa-status" class="text-input">
            <option value="pending">Pending</option><option value="approved">Approved</option><option value="rejected">Rejected</option>
          </select>
        </div>
        <ul class="leader-list" id="admin-wa"><li class="empty-state">None.</li></ul>
      </div>
    </div>
    <div class="tab-panel" data-apanel="withdrawals" hidden>
      <div class="card"><p class="card-title">Pending withdrawals</p><ul class="leader-list" id="admin-withdrawals"><li class="empty-state">None.</li></ul></div>
    </div>
    <div class="tab-panel" data-apanel="settings" hidden>
      <div class="card">
        <p class="card-title">Withdrawal timer</p>
        <label class="field-label mt-12" for="admin-timer-target">Target date/time</label>
        <input id="admin-timer-target" class="text-input" type="datetime-local"/>
        <div class="row-between mt-12">
          <label><input type="checkbox" id="admin-timer-enabled"/><span> Timer enabled</span></label>
          <button class="btn btn-primary btn-compact" id="admin-timer-save" type="button">Save timer</button>
        </div>
      </div>
      <div class="card">
        <p class="card-title">Add Wallet</p>
        <label class="field-label mt-12" for="admin-wa-enabled">Section</label>
        <select id="admin-wa-enabled" class="text-input">
          <option value="0">Locked</option><option value="1">Unlocked</option>
        </select>
        <label class="field-label mt-12" for="admin-wa-fee">Fee (USD)</label>
        <input id="admin-wa-fee" class="text-input" type="number" min="0" step="0.01"/>
        <button class="btn btn-primary mt-12" id="admin-wa-save" type="button">Save</button>
      </div>
      <div class="card">
        <p class="card-title">Referral settings</p>
        <label class="field-label mt-12" for="admin-ref-min">Minimum valid referrals</label>
        <input id="admin-ref-min" class="text-input" type="number" min="1" step="1"/>
        <label class="field-label mt-12" for="admin-ref-reward">Reward per milestone (USD)</label>
        <input id="admin-ref-reward" class="text-input" type="number" min="0" step="0.01"/>
        <button class="btn btn-primary mt-12" id="admin-ref-save" type="button">Save</button>
      </div>
      <div class="card">
        <p class="card-title">All settings</p>
        <ul class="kv-list" id="admin-settings"></ul>
        <button id="admin-settings-reload" class="btn btn-ghost mt-12" type="button">Reload</button>
      </div>
    </div>
  </div>
</main>
</div>
<div id="toast-host" class="toast-host" aria-live="polite"></div>
<div id="boot-loader" class="boot-loader"><p class="boot-text">Loading admin…</p></div>
<script src="/assets/js/config.js"></script>
<script src="/assets/js/api.js"></script>
<script src="/assets/js/telegram.js"></script>
<script src="/assets/js/ui.js"></script>
<script src="/admin/admin.js"></script>
</body>
</html>
'''

FILES["frontend/admin/admin.js"] = r'''(function(){
"use strict";
const API=window.Fox.api, TG=window.Fox.tg, U=window.Fox.ui;

function showAuthError(m){
  const b=document.getElementById("admin-auth-error"), t=document.getElementById("admin-auth-error-msg"), a=document.getElementById("admin-app");
  if(t) t.textContent=m; if(b) b.hidden=false; if(a) a.hidden=true; U.hideBootLoader();
}
function showAdmin(){ const b=document.getElementById("admin-auth-error"); if(b) b.hidden=true; const a=document.getElementById("admin-app"); if(a) a.hidden=false; }

async function authenticate(){
  if(!TG.isInsideTelegram()){ showAuthError("Open this panel from inside Telegram."); return false; }
  try{
    const res=await API.authenticate(TG.state.initData);
    if(!res || !res.token){ showAuthError("Authentication failed."); return false; }
    if(!res.is_admin){ showAuthError("This account is not an administrator."); return false; }
    API.setToken(res.token); showAdmin(); return true;
  } catch(err){ showAuthError(err.message||"Could not authenticate."); return false; }
}

async function fetchImage(url){
  const r=await fetch(url,{headers:{"Authorization":"Bearer "+API.getToken()},cache:"no-store"});
  if(!r.ok) throw new Error("image "+r.status);
  return URL.createObjectURL(await r.blob());
}

function bindTabs(){
  document.querySelectorAll("#admin-app .tab").forEach(t=>{
    if(t.dataset.bound==="1") return; t.dataset.bound="1";
    t.addEventListener("click",()=>{
      document.querySelectorAll("#admin-app .tab").forEach(x=>x.classList.remove("is-active"));
      t.classList.add("is-active");
      const tab=t.getAttribute("data-atab");
      document.querySelectorAll("#admin-app .tab-panel").forEach(p=>{ p.hidden=p.getAttribute("data-apanel")!==tab; });
    });
  });
}

async function loadOverview(){
  const host=document.getElementById("admin-stats"); if(!host) return;
  try{ const ov=await API.get("/api/admin/overview"); const s=ov.stats||{};
    host.innerHTML="<li><span>Total users</span><b>"+U.formatNumber(s.total_users||0)+"</b></li>"+
      "<li><span>Coins in circulation</span><b>"+U.formatNumber(s.total_coins||0)+"</b></li>"+
      "<li><span>Pending activations</span><b>"+U.formatNumber(s.pending_wallet_activations||0)+"</b></li>"+
      "<li><span>Pending withdrawals</span><b>"+U.formatNumber(s.pending_withdrawals||0)+"</b></li>";
  } catch(err){ host.innerHTML="<li><span>Error</span><b>"+U.escapeHtml(err.message)+"</b></li>"; }
}

async function loadActivations(){
  const host=document.getElementById("admin-wa"); if(!host) return;
  const st=(document.getElementById("admin-wa-status")||{}).value || "pending";
  try{
    const res=await API.get("/api/admin/wallet-activations?status="+encodeURIComponent(st)+"&limit=50");
    const rows=res.activations||[];
    if(!rows.length){ host.innerHTML='<li class="empty-state">No requests.</li>'; return; }
    host.innerHTML=rows.map(a=>{
      const shot=a.has_screenshot?'<div class="upload-preview" data-shot="'+a.id+'" style="margin-top:10px"><p class="card-hint" style="padding:12px">Loading…</p></div>':'';
      return '<li style="flex-direction:column;align-items:stretch"><div class="row-between"><span class="li-main">'+
        '<span class="li-name">'+U.escapeHtml((a.method||"").toUpperCase())+" · "+U.formatUSD(a.fee_cents||0)+'</span>'+
        '<span class="li-sub">'+U.escapeHtml(a.display_name||"User")+" · "+U.escapeHtml(U.formatDateTime(a.created_at))+'</span>'+
        '</span><span class="pill pill-amber">'+U.escapeHtml(a.status)+'</span></div>'+shot+
        '<div class="row-between mt-8"><button class="btn btn-primary btn-compact" data-wa-act="approve" data-wa-id="'+a.id+'">Approve</button>'+
        '<button class="btn btn-ghost btn-compact" data-wa-act="reject" data-wa-id="'+a.id+'">Reject</button></div></li>';
    }).join("");
    host.querySelectorAll("[data-wa-act]").forEach(b=>b.addEventListener("click",()=>waAction(b.getAttribute("data-wa-id"),b.getAttribute("data-wa-act"),b)));
    for(const a of rows){
      if(!a.has_screenshot) continue;
      const w=host.querySelector('[data-shot="'+a.id+'"]'); if(!w) continue;
      try{ const url=await fetchImage("/api/wallet/activate/"+a.id+"/screenshot"); w.innerHTML='<img src="'+url+'" alt="proof"/>'; }
      catch(e){ w.innerHTML='<p class="card-hint" style="padding:12px;color:#fecaca">Could not load.</p>'; }
    }
  } catch(err){ host.innerHTML='<li class="empty-state">'+U.escapeHtml(err.message||"Could not load.")+"</li>"; }
}

async function waAction(id, action, btn){
  let note="";
  if(action==="reject"){ note=window.prompt("Rejection reason:",""); if(note===null) return; }
  else { if(!window.confirm("Approve and activate wallet?")) return; }
  U.setLoading(btn,true,"…");
  try{ await API.post("/api/admin/wallet-activations/"+encodeURIComponent(id)+"/action",{action,note}); U.toast("Done.","success"); await loadActivations(); }
  catch(err){ U.toast(err.message||"Failed.","error"); }
  finally { U.setLoading(btn,false); }
}

async function loadWithdrawals(){
  const host=document.getElementById("admin-withdrawals"); if(!host) return;
  try{ const res=await API.get("/api/admin/withdrawals?status=pending&limit=50"); const rows=res.withdrawals||[];
    if(!rows.length){ host.innerHTML='<li class="empty-state">None pending.</li>'; return; }
    host.innerHTML=rows.map(w=>'<li style="flex-direction:column;align-items:stretch"><div class="row-between">'+
      '<span class="li-main"><span class="li-name">'+U.formatUSD(w.amount_cents)+" · "+U.escapeHtml(w.method)+'</span>'+
      '<span class="li-sub">'+U.escapeHtml(w.display_name||"User")+" · "+U.escapeHtml(U.formatDateTime(w.created_at))+'</span>'+
      '<span class="li-sub">Dest: '+U.escapeHtml(w.destination||"—")+'</span></span>'+
      '<span class="pill pill-amber">pending</span></div>'+
      '<div class="row-between mt-8"><button class="btn btn-primary btn-compact" data-wd-act="approve" data-wd-id="'+w.id+'">Approve</button>'+
      '<button class="btn btn-ghost btn-compact" data-wd-act="reject" data-wd-id="'+w.id+'">Reject</button>'+
      '<button class="btn btn-primary btn-compact" data-wd-act="paid" data-wd-id="'+w.id+'">Paid</button></div></li>').join("");
    host.querySelectorAll("[data-wd-act]").forEach(b=>b.addEventListener("click",()=>wdAction(b.getAttribute("data-wd-id"),b.getAttribute("data-wd-act"),b)));
  } catch(err){ host.innerHTML='<li class="empty-state">'+U.escapeHtml(err.message||"Failed.")+"</li>"; }
}

async function wdAction(id, action, btn){
  if(!window.confirm("Confirm: "+action+"?")) return;
  U.setLoading(btn,true,"…");
  try{ await API.post("/api/admin/withdrawals/"+encodeURIComponent(id)+"/action",{action,note:""}); U.toast("Done.","success"); await loadWithdrawals(); }
  catch(err){ U.toast(err.message||"Failed.","error"); }
  finally { U.setLoading(btn,false); }
}

async function loadSettings(){
  try{
    const res=await API.get("/api/admin/settings"); const items=res.settings||[];
    const map={}; items.forEach(s=>map[s.key]=s.value);
    const tmr=document.getElementById("admin-timer-target"); if(tmr && map.withdrawal_target_local) tmr.value=map.withdrawal_target_local;
    const tme=document.getElementById("admin-timer-enabled"); if(tme) tme.checked=map.withdrawal_timer_enabled==="1";
    const wa=document.getElementById("admin-wa-enabled"); if(wa) wa.value=map.wallet_activation_enabled==="1"?"1":"0";
    const wf=document.getElementById("admin-wa-fee"); if(wf) wf.value=(parseInt(map.wallet_activation_fee_cents||"0",10)/100).toFixed(2);
    const rmin=document.getElementById("admin-ref-min"); if(rmin) rmin.value=map.referral_min_valid||"3";
    const rrew=document.getElementById("admin-ref-reward"); if(rrew) rrew.value=(parseInt(map.referral_reward_cents||"1000",10)/100).toFixed(2);
    const sh=document.getElementById("admin-settings");
    if(sh) sh.innerHTML=items.map(s=>"<li><span>"+U.escapeHtml(s.key)+"</span><b>"+U.escapeHtml(String(s.value).slice(0,80))+"</b></li>").join("");
  } catch(err){}
  try{ const res=await API.get("/api/admin/audit?limit=50"); const rows=res.logs||[];
    const h=document.getElementById("admin-audit");
    if(h) h.innerHTML=rows.length?rows.map(l=>'<li><span class="li-main"><span class="li-name">'+U.escapeHtml(l.action)+'</span><span class="li-sub">'+U.escapeHtml(l.actor||"system")+" · "+U.escapeHtml(U.formatDateTime(l.created_at))+'</span></span></li>').join(""):'<li class="empty-state">No entries.</li>';
  } catch(err){}
}

function bindButtons(){
  const t=document.getElementById("admin-timer-save");
  if(t) t.addEventListener("click", async ()=>{
    const dt=document.getElementById("admin-timer-target").value; const en=document.getElementById("admin-timer-enabled").checked;
    try{ await API.post("/api/admin/withdrawal-timer",{target_local:dt, enabled:en}); U.toast("Saved.","success"); loadSettings(); }
    catch(e){ U.toast(e.message||"Failed.","error"); }
  });
  const wa=document.getElementById("admin-wa-save");
  if(wa) wa.addEventListener("click", async ()=>{
    const en=document.getElementById("admin-wa-enabled").value; const fee=parseFloat(document.getElementById("admin-wa-fee").value||"0");
    try{ await API.post("/api/admin/settings",{updates:{wallet_activation_enabled:en, wallet_activation_fee_cents:String(Math.round(fee*100))}}); U.toast("Saved.","success"); loadSettings(); }
    catch(e){ U.toast(e.message||"Failed.","error"); }
  });
  const r=document.getElementById("admin-ref-save");
  if(r) r.addEventListener("click", async ()=>{
    const minv=document.getElementById("admin-ref-min").value; const reward=parseFloat(document.getElementById("admin-ref-reward").value||"0");
    try{ await API.post("/api/admin/settings",{updates:{referral_min_valid:String(minv), referral_reward_cents:String(Math.round(reward*100))}}); U.toast("Saved.","success"); loadSettings(); }
    catch(e){ U.toast(e.message||"Failed.","error"); }
  });
  const sr=document.getElementById("admin-settings-reload"); if(sr) sr.addEventListener("click",()=>loadSettings());
  const sel=document.getElementById("admin-wa-status"); if(sel) sel.addEventListener("change",()=>loadActivations());
}

async function boot(){
  U.init(); TG.init();
  if(!await authenticate()) return;
  bindTabs(); bindButtons();
  await Promise.all([loadOverview(), loadActivations(), loadWithdrawals(), loadSettings()]);
  U.hideBootLoader();
}
if(document.readyState==="loading") document.addEventListener("DOMContentLoaded",boot);
else boot();
})();
'''

FILES["uploads/.gitkeep"] = ""

# ============================================================================
# WRITER
# ============================================================================
def write_all():
    written = 0
    for rel, content in FILES.items():
        p = ROOT / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(content if content.startswith("\n") else content, encoding="utf-8")
        written += 1
    return written


def main():
    print("FOX EARN setup")
    print(f"Creating project at: {ROOT}")
    print()

    if ROOT.exists() and any(ROOT.iterdir()):
        print("Note: folder exists. Existing files will be overwritten.")
        print()

    n = write_all()
    print(f"Wrote {n} files.")
    print()

    # Copy .env.example to .env if missing
    env = ROOT / ".env"
    if not env.exists():
        ex = ROOT / ".env.example"
        if ex.exists():
            env.write_text(ex.read_text(encoding="utf-8"), encoding="utf-8")
            print("[ok] created .env from .env.example")

    print()
    print("=" * 68)
    print(" NEXT STEPS")
    print("=" * 68)
    print()
    print("1. EDIT .env and set:")
    print(f"     {env}")
    print("        BOT_TOKEN           = from @BotFather")
    print("        ADMIN_TELEGRAM_IDS  = your numeric Telegram ID")
    print("        FRONTEND_ORIGINS    = http://127.0.0.1:8000,http://localhost:8000")
    print()
    print("2. Run locally:")
    print(f"     cd {ROOT.name}")
    print("     python run.py")
    print("     Open http://127.0.0.1:8000/")
    print()
    print("3. Deploy on PythonAnywhere:")
    print(f"     See {ROOT.name}/RUN_ON_PYTHONANYWHERE.md")
    print()
    print("4. Admin panel URL:")
    print("     http://127.0.0.1:8000/admin/")
    print("     https://YOUR_USERNAME.pythonanywhere.com/admin/")
    print()


if __name__ == "__main__":
    main()