#!/usr/bin/env python3
"""Run idempotent schema migrations.

Usage (from backend/):
  python scripts/migrate_orders_schema.py
"""

from __future__ import annotations

import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

from database import engine  # noqa: E402
from services.schema_migration import migrate_schema  # noqa: E402


def main() -> None:
    migrate_schema(engine)
    print("OK: schema migration complete")


if __name__ == "__main__":
    main()
