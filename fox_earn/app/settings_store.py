from __future__ import annotations
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
