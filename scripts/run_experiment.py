#!/usr/bin/env python3
"""Run a method grid. Default is dry-run (no mock scores)."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from beacon.rollout import main as rollout_main  # noqa: E402

if __name__ == "__main__":
    rollout_main()
