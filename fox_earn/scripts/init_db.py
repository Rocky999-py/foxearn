#!/usr/bin/env python3
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
