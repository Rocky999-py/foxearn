from __future__ import annotations
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
    locked = Column(BigInteger, default=0, nullable=False)
    total_earned = Column(BigInteger, default=0, nullable=False)
    referred_by_id = Column(Integer, nullable=True)
    is_banned = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime(timezone=True), default=utcnow, nullable=False)
    updated_at = Column(DateTime(timezone=True), default=utcnow, onupdate=utcnow, nullable=False)

    @property
    def display_name(self) -> str:
        name = " ".join(filter(None, [self.first_name, self.last_name])).strip()
        return name or (self.username and ("@" + self.username)) or f"Fox #{self.id}"

    @property
    def withdrawable(self) -> int:
        return max(0, int(self.balance or 0) - int(self.locked or 0))


class SessionToken(Base):
    __tablename__ = "session_tokens"
    id = Column(Integer, primary_key=True)
    token = Column(String(64), unique=True, index=True, nullable=False)
    user_id = Column(Integer, index=True, nullable=False)
    expires_at = Column(BigInteger, nullable=False)
    created_at = Column(DateTime(timezone=True), default=utcnow, nullable=False)


class TapDay(Base):
    __tablename__ = "tap_days"
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, index=True, nullable=False)
    day = Column(String(10), index=True, nullable=False)
    count = Column(Integer, default=0, nullable=False)
    __table_args__ = (UniqueConstraint("user_id", "day", name="uq_tap_day"),)


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
    label = Column(String(128), nullable=False)
    amount = Column(BigInteger, nullable=False)
    status = Column(String(16), default="completed", nullable=False)
    ref = Column(String(64), nullable=True)
    created_at = Column(DateTime(timezone=True), default=utcnow, nullable=False, index=True)


class Task(Base):
    __tablename__ = "tasks"
    id = Column(Integer, primary_key=True)
    title = Column(String(160), nullable=False)
    description = Column(Text, nullable=True)
    reward = Column(Integer, default=2, nullable=False)
    url = Column(String(512), nullable=True)
    verification_type = Column(String(32), default="link_open", nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    expires_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), default=utcnow, nullable=False)


class TaskCompletion(Base):
    __tablename__ = "task_completions"
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, index=True, nullable=False)
    task_id = Column(Integer, index=True, nullable=False)
    status = Column(String(16), default="pending", nullable=False)
    reward = Column(Integer, default=0, nullable=False)
    created_at = Column(DateTime(timezone=True), default=utcnow, nullable=False)
    reviewed_at = Column(DateTime(timezone=True), nullable=True)
    __table_args__ = (UniqueConstraint("user_id", "task_id", name="uq_task_once"),)


class Referral(Base):
    __tablename__ = "referrals"
    id = Column(Integer, primary_key=True)
    referrer_id = Column(Integer, index=True, nullable=False)
    referred_id = Column(Integer, unique=True, nullable=False)
    status = Column(String(16), default="pending", nullable=False)
    rewarded = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime(timezone=True), default=utcnow, nullable=False)


class Withdrawal(Base):
    __tablename__ = "withdrawals"
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, index=True, nullable=False)
    amount = Column(BigInteger, nullable=False)
    method = Column(String(32), nullable=False)
    destination = Column(String(256), nullable=False)
    status = Column(String(16), default="pending", nullable=False)
    note = Column(Text, nullable=True)
    refunded = Column(Boolean, default=False, nullable=False)
    paid_at = Column(DateTime(timezone=True), nullable=True)
    screenshot_path = Column(String(512), nullable=True)
    created_at = Column(DateTime(timezone=True), default=utcnow, nullable=False, index=True)
    updated_at = Column(DateTime(timezone=True), default=utcnow, onupdate=utcnow, nullable=False)


class DepositRequest(Base):
    __tablename__ = "deposit_requests"
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, index=True, nullable=False)
    amount = Column(BigInteger, nullable=True)
    asset = Column(String(16), nullable=True)
    network = Column(String(32), nullable=True)
    method = Column(String(32), default="binance_pay")
    tx_id = Column(String(128), nullable=True)
    user_note = Column(Text, nullable=True)
    admin_note = Column(Text, nullable=True)
    status = Column(String(24), default="awaiting_proof", index=True)
    screenshot_path = Column(String(512), nullable=True)
    coins_credited = Column(BigInteger, default=0, nullable=False)
    reviewed_by_telegram_id = Column(BigInteger, nullable=True)
    reviewed_at = Column(DateTime(timezone=True), nullable=True)
    expires_at = Column(DateTime(timezone=True), nullable=False)
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
Index("ix_dep_user_created", DepositRequest.user_id, DepositRequest.created_at.desc())
