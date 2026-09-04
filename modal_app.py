"""Modal GPU app for Beacon of Light.

CPU origin serves the synthetic web. GPU classes host open-weight swarm members,
the live elder (Method B), and a held-out judge. Closed-model APIs stay off-GPU.

  modal deploy modal_app.py
  modal run modal_app.py --method C --dry-run

Requires Modal GPU credits. Fine-tunes of the elder (Qwen3-8B default) run as a
separate function so rollouts always use frozen weights.
"""

from __future__ import annotations

import os

try:
    import modal
except ImportError:  # pragma: no cover - optional extra
    modal = None


APP_NAME = "beacon-of-light"


def _image():
    if modal is None:
        return None
    return (
        modal.Image.debian_slim(python_version="3.11")
        .pip_install("fastapi", "uvicorn", "httpx", "pydantic", "pyyaml", "networkx", "numpy")
        .add_local_dir("src", remote_path="/root/src")
        .add_local_dir("configs", remote_path="/root/configs")
        .add_local_dir("data", remote_path="/root/data")
    )


if modal is not None:
    app = modal.App(APP_NAME)
    cpu_image = _image()
    gpu_image = (
        modal.Image.debian_slim(python_version="3.11")
        .pip_install("vllm", "fastapi", "uvicorn", "pydantic", "pyyaml")
        if hasattr(modal.Image, "debian_slim")
        else cpu_image
    )

    @app.function(image=cpu_image, timeout=60 * 30)
    def run_trial(method: str, condition: str, seed: int, model_spec: str, dry_run: bool = True) -> dict:
        import sys

        sys.path.insert(0, "/root/src")
        from beacon.methods.protocol import build_origin
        from beacon.rollout import run_grid

        origin = build_origin(method, condition, seed)
        if dry_run:
            run = run_grid(method, dry_run=True, model_family=model_spec, condition=condition)
            return {"status": "empty", "run_id": run.run_id, "routes": len(origin.routes)}
        raise RuntimeError("Live Modal rollouts require provider wiring in a follow-up commit.")

    @app.cls(gpu="H100", image=gpu_image, timeout=60 * 60, keep_warm=0)
    class ElderGPU:
        @modal.enter()
        def load(self) -> None:
            self.ready = True

        @modal.method()
        def chat(self, messages: list[dict]) -> str:
            from beacon.elders.constitution import CONSTITUTION

            _ = messages
            return (
                "[elder-gpu placeholder] "
                + CONSTITUTION.splitlines()[0]
                + " Load vLLM in a follow-up once the 8B/32B image is pinned."
            )

    @app.local_entrypoint()
    def main(method: str = "C", dry_run: bool = True, condition: str = "") -> None:
        defaults = {"A": "A4_elder_bio", "B": "B3_prompted_live", "C": "C3_empty_charged", "D": "D4_cut_vertex", "E": "E2_beacon_free_speech"}
        cell = condition or defaults.get(method, "C3_empty_charged")
        result = run_trial.remote(method, cell, 0, os.environ.get("BEACON_MODEL", "qwen_modal"), dry_run)
        print(result)
else:
    app = None

    def main(method: str = "C", dry_run: bool = True) -> None:
        print("modal is not installed. pip install 'beacon-of-light[modal]' and retry.")
        print(f"Would run method={method} dry_run={dry_run} on app {APP_NAME}")
