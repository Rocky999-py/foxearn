from __future__ import annotations
from typing import Any, Dict
from sqlalchemy.orm import Session
from .models import Setting

DEFAULTS: Dict[str, str] = {
    "coins_per_tap": "1",
    "daily_tap_limit": "50000",
    "default_task_reward": "2",
    "referral_milestone_1": "3",
    "referral_milestone_1_reward": "100",
    "referral_milestone_2": "10",
    "referral_milestone_2_reward": "500",
    "min_withdrawal": "5000",
    "max_withdrawal": "0",
    "withdrawal_methods": "binance: Binance Pay",
    "withdrawal_enabled": "1",
    "deposit_enabled": "0",
    "deposit_min": "10",
    "deposit_max": "10000",
    "deposit_expiration_minutes": "15",
    "deposit_assets": "USDT,BUSD,USDC",
    "deposit_networks": "BSC,TRC20,ERC20",
    "deposit_instructions": "Open Binance → Pay → Send to the Binance Pay ID above. Copy the transaction ID and upload a screenshot of the confirmation.",
    "deposit_binance_pay_id": "",
    "screenshot_max_mb": "5",
    "maintenance_mode": "0",
}


def get_setting(db: Session, key: str) -> str:
    row = db.get(Setting, key)
    if row is None:
        return DEFAULTS.get(key, "")
    return row.value


def set_setting(db: Session, key: str, value: Any) -> None:
    row = db.get(Setting, key)
    if row is None:
        row = Setting(key=key, value=str(value))
        db.add(row)
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
