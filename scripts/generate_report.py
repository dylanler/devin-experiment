#!/usr/bin/env python3
"""Print experiment-store status. Empty tables are reported as empty."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from beacon.logstore import db_path, empty_message, init_db, table_counts  # noqa: E402


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--db", type=Path, default=None)
    args = parser.parse_args()
    path = args.db or db_path()
    if not path.exists():
        init_db(path)
    print(f"Store: {path}")
    counts = table_counts(path)
    filled = {k: v for k, v in counts.items() if v}
    if not filled:
        print("No evaluation scores yet. Tables are currently empty.")
    for table, n in counts.items():
        print(f"  {table}: {empty_message(table)}" if n == 0 else f"  {table}: {n} rows")


if __name__ == "__main__":
    main()
