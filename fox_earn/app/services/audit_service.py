from __future__ import annotations
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
