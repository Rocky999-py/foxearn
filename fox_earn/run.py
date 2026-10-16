#!/usr/bin/env python3
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
