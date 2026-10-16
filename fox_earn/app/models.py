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
