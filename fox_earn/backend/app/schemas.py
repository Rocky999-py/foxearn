from __future__ import annotations
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


class TapOut(BaseModel):
    accepted: int
    balance: int
    withdrawable: int
    taps_used_today: int
    daily_tap_limit: int


class TaskClaimIn(BaseModel):
    idempotency_key: Optional[str] = None


class WithdrawalIn(BaseModel):
    amount: int = Field(gt=0)
    method: str = Field(min_length=1, max_length=32)
    destination: str = Field(min_length=1, max_length=256)
    idempotency_key: Optional[str] = None


class DepositStartIn(BaseModel):
    pass


class DepositSubmitIn(BaseModel):
    amount: float = Field(gt=0)
    asset: str = Field(min_length=1, max_length=16)
    network: str = Field(min_length=1, max_length=32)
    tx_id: str = Field(min_length=1, max_length=128)
    user_note: Optional[str] = ""
    screenshot_base64: Optional[str] = None


class AdminWithdrawalAction(BaseModel):
    action: str
    note: Optional[str] = ""


class AdminDepositAction(BaseModel):
    action: str
    note: Optional[str] = ""
