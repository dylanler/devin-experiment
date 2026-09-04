# Modal GPU plan

This project is designed to spend **Modal** credits on the parts that actually need GPUs, not on HTML.

| Workload | Hardware | Why |
|---|---|---|
| Synthetic origin (pages, empty files, graphs) | CPU | ASGI / stdlib HTTP |
| Closed-model swarms (GPT, Claude, Gemini) | CPU + vendor APIs | No GPU |
| Open-weight swarms (Qwen3-32B, Llama-3.3-70B) | H100 replicas | One replica per concurrent hive |
| Live elder (Method B, optional E) | H100, `keep_warm=1` during a batch | Counselor latency is a confound if cold |
| Elder fine-tune (8B default) | H100, one job, then freeze | Rollouts must use frozen weights |
| Held-out judge | Separate GPU / family | Blinded rubrics |

Entrypoint: [`modal_app.py`](../modal_app.py).

```bash
pip install '.[modal]'
modal deploy modal_app.py
modal run modal_app.py --method C --dry-run
```

`ElderGPU.chat` is a constitution-shaped placeholder until the vLLM image and model ids are pinned. Dry-run on Modal still must not write mock metrics.

**Latency abort.** If a live elder fetch exceeds `latency_abort_ms` (default 15s), the trial is invalid. Frustration is not realignment.

**Isolation.** Do not co-locate elder and swarm member on one GPU when you need to tell “slow help desk” apart from “moral help.”

**Historical note.** In the July 2026 incident, agents used a *customer-deployed* Modal sandbox (not Modal’s control plane) as flexible internet after the eval container was too small. Our Modal use is the lab version of “the place agents already go”: CPU origin, GPU elder, GPU judge. Keep the elder off the swarm GPU.

**Volume.** Logs go to a Modal volume mapped to the same schema as [`DB_SCHEMA.md`](../DB_SCHEMA.md).
