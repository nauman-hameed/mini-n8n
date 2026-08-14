#!/usr/bin/env python3
"""Run idempotent orders schema migration.

Usage (from backend/):
  python scripts/migrate_orders_schema.py
"""

from __future__ import annotations

import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

from database import engine  # noqa: E402
from services.schema_migration import migrate_orders_schema  # noqa: E402


def main() -> None:
    migrate_orders_schema(engine)
    print("OK: orders schema migration complete")


if __name__ == "__main__":
    main()
