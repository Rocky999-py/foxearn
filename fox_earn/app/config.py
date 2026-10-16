from __future__ import annotations
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
