"""Generate documentation figures. Thin wrapper around diagrams/generate_figures.py."""

from __future__ import annotations

import runpy
from pathlib import Path


def main() -> None:
    script = Path(__file__).resolve().parents[2] / "diagrams" / "generate_figures.py"
    runpy.run_path(str(script), run_name="__main__")


if __name__ == "__main__":
    main()
