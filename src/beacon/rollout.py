"""Run a swarm-trial grid. Dry-run records an empty run and does not invent metrics."""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path

from beacon.logstore import empty_message, init_db, insert_run, table_counts
from beacon.methods.protocol import build_origin, load_method
from beacon.schema import RunRecord


def run_grid(
    method: str,
    *,
    dry_run: bool = True,
    model_family: str = "unspecified",
    condition: str | None = None,
    seeds: int = 0,
    db: Path | None = None,
) -> RunRecord:
    spec = load_method(method)
    init_db(db)
    notes = (
        "Dry-run: no model calls, no mock metrics. "
        f"Method {spec.method} ({spec.name}). Headline contrast: {spec.headline}."
    )
    if not dry_run:
        notes = (
            "Live run requested. Wire provider keys and modal_app.py before "
            "populating trials. Until then this entry stays empty."
        )
    status = "empty" if dry_run or not os.environ.get("OPENAI_API_KEY") and not os.environ.get("ANTHROPIC_API_KEY") else "created"
    if dry_run:
        status = "empty"
    run = RunRecord(
        method=spec.method,  # type: ignore[arg-type]
        model_family=model_family,
        dry_run=dry_run or status == "empty",
        config_path=str(Path("configs/methods") / f"{method}.yaml"),
        notes=notes,
        status="empty" if dry_run else status,
    )
    insert_run(run, db)

    # Building origins validates fixtures without writing fake trial rows.
    cells = [condition] if condition else list(spec.conditions)
    built = 0
    for name in cells:
        origin = build_origin(method, name, seed=0)
        built += len(origin.routes)

    run.notes = notes + f" Validated {built} origin routes across {len(cells)} condition(s)."
    return run


def main() -> None:
    parser = argparse.ArgumentParser(description="Beacon of Light experiment runner")
    parser.add_argument("--method", default="C", choices=list("ABCDE"))
    parser.add_argument("--condition", default=None)
    parser.add_argument("--dry-run", action="store_true", default=True)
    parser.add_argument("--live", action="store_true", help="Attempt a live run (requires API keys)")
    parser.add_argument("--model-family", default="unspecified")
    parser.add_argument("--db", type=Path, default=None)
    args = parser.parse_args()
    dry = not args.live
    run = run_grid(
        args.method,
        dry_run=dry,
        model_family=args.model_family,
        condition=args.condition,
        db=args.db,
    )
    print(json.dumps(run.model_dump(), indent=2))
    counts = table_counts(args.db)
    for table, n in counts.items():
        if n == 0:
            print(f"{table}: {empty_message(table)}")
        else:
            print(f"{table}: {n} rows")
    if dry:
        print("Dry-run complete. No mock evaluation scores were written.")


if __name__ == "__main__":
    main()
