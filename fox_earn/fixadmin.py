#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Remove the unused Task import from app/api/admin.py."""

from pathlib import Path

TARGET = Path(__file__).resolve().parent / "app" / "api" / "admin.py"

if not TARGET.exists():
    print("ERROR: app/api/admin.py not found. Run from the project root.")
    raise SystemExit(1)

src = TARGET.read_text(encoding="utf-8")

# 1) Fix the import line
old_import = "from ..models import User, Withdrawal, WalletActivationRequest, Task, Setting, AuditLog"
new_import = "from ..models import User, Withdrawal, WalletActivationRequest, Setting, AuditLog"

if old_import in src:
    src = src.replace(old_import, new_import)
    print("[ok] fixed import line")
elif new_import in src:
    print("[skip] import already correct")
else:
    # fallback: any line starting with the import
    lines = src.splitlines()
    for i, line in enumerate(lines):
        if line.strip().startswith("from ..models import"):
            lines[i] = new_import
            print(f"[ok] replaced line {i+1}")
            break
    src = "\n".join(lines)

# 2) Remove the list_tasks endpoint if present
marker_start = '@router.get("/admin/tasks")'
if marker_start in src:
    lines = src.splitlines()
    out = []
    skip = False
    for i, line in enumerate(lines):
        if line.strip() == marker_start.strip():
            # Skip until we hit the next top-level @router or blank-blank
            skip = True
            continue
        if skip:
            # Stop skipping when we hit the next decorator
            if line.startswith("@router."):
                skip = False
                out.append(line)
                continue
            # Also stop at a top-level def/class
            if line and not line.startswith(" ") and not line.startswith("@") and not line.startswith("def"):
                skip = False
                out.append(line)
                continue
            continue
        out.append(line)
    src = "\n".join(out)
    print("[ok] removed /admin/tasks endpoint")
else:
    print("[skip] no /admin/tasks endpoint to remove")

TARGET.write_text(src, encoding="utf-8")
print(f"\nPatched: {TARGET}")
print("Restart the backend.")