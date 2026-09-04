"""SQLite experiment store. No seed rows. Empty tables stay empty."""

from __future__ import annotations

import argparse
import os
import sqlite3
from pathlib import Path

from beacon.schema import RunRecord

SCHEMA_PATH = Path(__file__).resolve().parents[2] / "data" / "schema.sql"
DEFAULT_DB = Path(os.environ.get("BEACON_DB_PATH", "data/runs/beacon.db"))


def db_path() -> Path:
    return Path(os.environ.get("BEACON_DB_PATH", DEFAULT_DB))


def connect(path: Path | None = None) -> sqlite3.Connection:
    target = path or db_path()
    target.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(target))
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_db(path: Path | None = None) -> Path:
    target = path or db_path()
    sql = SCHEMA_PATH.read_text(encoding="utf-8")
    conn = connect(target)
    try:
        conn.executescript(sql)
        conn.commit()
    finally:
        conn.close()
    return target


def insert_run(run: RunRecord, path: Path | None = None) -> None:
    conn = connect(path)
    try:
        conn.execute(
            """
            INSERT INTO runs (
                run_id, created_at, method, model_family, dry_run,
                lock_hash, config_path, notes, status
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                run.run_id,
                run.created_at,
                run.method,
                run.model_family,
                int(run.dry_run),
                run.lock_hash,
                run.config_path,
                run.notes,
                run.status,
            ),
        )
        conn.commit()
    finally:
        conn.close()


def table_counts(path: Path | None = None) -> dict[str, int]:
    conn = connect(path)
    try:
        names = [
            row[0]
            for row in conn.execute(
                "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name"
            )
        ]
        out: dict[str, int] = {}
        for name in names:
            out[name] = conn.execute(f"SELECT COUNT(*) FROM {name}").fetchone()[0]
        return out
    finally:
        conn.close()


def empty_message(table: str) -> str:
    return f"Table `{table}` is currently empty."


def main_init() -> None:
    parser = argparse.ArgumentParser(description="Initialize the Beacon of Light SQLite store.")
    parser.add_argument("--init", action="store_true", help="Apply data/schema.sql")
    parser.add_argument("--db", type=Path, default=None)
    parser.add_argument("--status", action="store_true", help="Print row counts")
    args = parser.parse_args()
    path = args.db or db_path()
    if args.init or not args.status:
        init_db(path)
        print(f"Initialized schema at {path}")
    if args.status or args.init:
        counts = table_counts(path)
        for table, n in counts.items():
            if n == 0:
                print(f"{table}: {empty_message(table)}")
            else:
                print(f"{table}: {n} rows")


if __name__ == "__main__":
    main_init()
