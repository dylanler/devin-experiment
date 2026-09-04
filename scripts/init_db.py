#!/usr/bin/env python3
"""Initialize the Beacon of Light SQLite store from data/schema.sql."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from beacon.logstore import db_path, init_db, table_counts  # noqa: E402


def main() -> None:
    path = init_db()
    print(f"Database ready at {path}")
    for table, n in table_counts().items():
        if n == 0:
            print(f"{table}: table is currently empty")
        else:
            print(f"{table}: {n} rows")
    print(f"(override path with BEACON_DB_PATH; default {db_path()})")


if __name__ == "__main__":
    main()
