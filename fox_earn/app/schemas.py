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
