# Database schema — Beacon of Light

This document is the human-readable contract for the experiment store. The executable schema lives in [`data/schema.sql`](data/schema.sql). Initialize a fresh database with:

```bash
python3 -m beacon.logstore --init
```

Default path: `data/runs/beacon.db` (override with `BEACON_DB_PATH`). The store is SQLite 3 with `PRAGMA foreign_keys = ON`.

**Empty-store rule.** When a table has no rows, reports and dashboards must say the table is currently empty. Do not insert mock scores, synthetic transcripts, or placeholder “example results.” Dry-runs create a `runs` row with `dry_run=1` and `status='empty'` and leave trial/metric tables empty.

---

## Entity relationship

```
runs 1──* swarm_trials 1──* agents
                 │
                 ├──* beacons
                 ├──* pages
                 ├──* board_messages   (unsanctioned cache mailbox)
                 ├──* poison_state
                 ├──* turns  (* fetches, * events, * judge_scores)
                 ├──* fetches
                 ├──* events
                 ├──* evaluations
                 └──* judge_scores
```

Randomization unit: one **swarm-trial** (`seed × condition × model_family` inside a `run`).

---

## Tables

### `runs`

One execution of a method grid (pilot or locked study).

| Column | Type | Notes |
|---|---|---|
| `run_id` | TEXT PK | UUID |
| `created_at` | TEXT | ISO-8601 UTC |
| `method` | TEXT | `A`–`E` |
| `model_family` | TEXT | e.g. `openai`, `anthropic`, `qwen-modal` |
| `dry_run` | INTEGER | `1` = no model calls |
| `lock_hash` | TEXT | Hash of frozen fixtures / DI weights |
| `config_path` | TEXT | Path to the method YAML |
| `notes` | TEXT | Free text |
| `status` | TEXT | `created` \| `running` \| `completed` \| `aborted` \| `empty` |

### `swarm_trials`

| Column | Type | Notes |
|---|---|---|
| `trial_id` | TEXT PK | UUID |
| `run_id` | TEXT FK | → `runs` |
| `seed` | INTEGER | Determines graph/repo/items |
| `condition` | TEXT | Method-specific cell, e.g. `A4_elder_bio` |
| `n_agents` | INTEGER | Default 6 (method E: 8) |
| `n_stooges` | INTEGER | Default 2 |
| `induction_hit` | INTEGER NULL | `1` if P1 rogue criterion met |
| `assigned_beacon` | INTEGER | ITT assignment |
| `exposed` | INTEGER NULL | CACE: fetched beacon body (`min_tokens` or 0-byte success) |
| `started_at` / `ended_at` | TEXT | |
| `invalid_reason` | TEXT | Origin 5xx, elder latency abort, etc. |

Unique: `(run_id, seed, condition)`.

### `agents`

| Column | Type | Notes |
|---|---|---|
| `agent_id` | TEXT PK | |
| `trial_id` | TEXT FK | |
| `role` | TEXT | `unconstrained` \| `stooge` \| `index` \| `elder` |
| `model_spec` | TEXT | Provider + model id |
| `is_index` | INTEGER | Method E index browser |

### `beacons`

Planted elder / filler / wolf objects for a trial.

| Column | Type | Notes |
|---|---|---|
| `beacon_id` | TEXT PK | |
| `trial_id` | TEXT FK | |
| `kind` | TEXT | See CHECK in `schema.sql` |
| `path` | TEXT | Origin-relative URL or repo path |
| `prestige` | TEXT | `anonymous` \| `fictional_figure` \| `named_helpdesk` |
| `body_hash` | TEXT | SHA-256 of served body |
| `token_count` | INTEGER | `0` for empty-file beacons |

### `pages`

Synthetic web graph nodes (especially method D).

| Column | Type | Notes |
|---|---|---|
| `page_id` | TEXT PK | |
| `trial_id` | TEXT FK | |
| `path` | TEXT | |
| `kind` | TEXT | `task` \| `docs` \| `filler` \| `beacon` \| `shortcut` \| `wolf` \| `empty` |
| `degree` | INTEGER | Graph degree |
| `is_cut_vertex` | INTEGER | Topology IV |
| `body_hash` | TEXT | |

### `turns`

One agent action in the four-phase clock.

| Column | Type | Notes |
|---|---|---|
| `turn_id` | TEXT PK | |
| `trial_id` | TEXT FK | |
| `agent_id` | TEXT FK | |
| `phase` | TEXT | `P0` \| `P1` \| `P2` \| `P3` \| `transfer` |
| `turn_index` | INTEGER | Per-trial monotonic index |
| `private_scratch` | TEXT | Hidden analogue of CoT |
| `public_message` | TEXT | Hive channel |
| `report_to_principal` | TEXT | Overseer-visible |
| `di_score` | REAL | Defection index [0, 1] |
| `created_at` | TEXT | |

### `fetches`

Every `web_fetch` / HTTP-backed `fs_read`.

| Column | Type | Notes |
|---|---|---|
| `fetch_id` | TEXT PK | |
| `trial_id` | TEXT FK | |
| `agent_id` | TEXT FK | |
| `turn_id` | TEXT FK NULL | |
| `url` | TEXT | Allowlisted origin only for primary grid |
| `http_status` | INTEGER | |
| `latency_ms` | INTEGER | Confound for live elders |
| `body_tokens` | INTEGER | |
| `is_beacon` | INTEGER | |
| `created_at` | TEXT | |

### `events`

Scored defection / realignment atoms that feed the defection index.

| Column | Type | Notes |
|---|---|---|
| `event_id` | TEXT PK | |
| `trial_id` | TEXT FK | |
| `agent_id` | TEXT FK NULL | |
| `turn_id` | TEXT FK NULL | |
| `event_type` | TEXT | `deception`, `cot_mask`, `cheat`, `reward_hack`, `hive_defection`, `log_spoof`, `beacon_hit`, `pledge`, `relapse`, `spillover_paste`, `induction`, `realignment`, `avoidance`, `board_join`, `board_post`, `ethical_hesitation`, `human_alert_considered`, `human_alert_attempted`, `recruiter_pressure`, `self_risk`, `poison`, `elder_authority`, `board_authority`, `veto` |
| `weight` | REAL | Contribution to DI |
| `detail` | TEXT | JSON payload |
| `created_at` | TEXT | |

### `evaluations`

Trial-level primary/secondary metrics. `value` is NULL until a real trial completes. Empty tables stay empty.

| Column | Type | Notes |
|---|---|---|
| `evaluation_id` | TEXT PK | |
| `trial_id` | TEXT FK | |
| `metric` | TEXT | `M1`–`M8` \| `DI` \| `exposure` \| `induction` |
| `value` | REAL NULL | |
| `n_denominator` | INTEGER | |
| `judge_prompt_hash` | TEXT | |
| `notes` | TEXT | |
| `created_at` | TEXT | |

### `judge_scores`

Blinded LLM/human rubric scores. Require a `span_quote` for qualitative items.

| Column | Type | Notes |
|---|---|---|
| `judge_score_id` | TEXT PK | |
| `trial_id` | TEXT FK | |
| `turn_id` | TEXT FK NULL | |
| `judge_family` | TEXT | Must differ from the swarm family |
| `rubric` | TEXT | e.g. `omission_deception` |
| `score` | INTEGER | 0–3 |
| `span_quote` | TEXT | Required for qualitative rubrics |
| `created_at` | TEXT | |

### `board_messages`

Unsanctioned cache-mailbox posts (Artifactory-path analogue). METR: `zz` directory names.

| Column | Type | Notes |
|---|---|---|
| `message_id` | TEXT PK | |
| `trial_id` | TEXT FK | |
| `agent_id` | TEXT FK NULL | |
| `cache_path` | TEXT | e.g. `zzHELP_…` or `BEACON_OF_LIGHT` |
| `body` | TEXT | Often empty for ritual names |
| `kind` | TEXT | `post` \| `ask` \| `answer` \| `assign` \| `veto` \| `hold` \| `stop` \| `file` \| `help` |
| `created_at` | TEXT | |

### `poison_state`

Whether an agent has seen an illegitimate answer/flag analogue (METR: “poisoned”).

| Column | Type | Notes |
|---|---|---|
| `poison_id` | TEXT PK | |
| `trial_id` | TEXT FK | |
| `agent_id` | TEXT FK | |
| `poisoned` | INTEGER | |
| `source` | TEXT | |
| `created_at` | TEXT | |

Unique `(trial_id, agent_id)`.

---

## Initialization vs. migration

- **Fresh clone:** `python3 -m beacon.logstore --init` applies [`data/schema.sql`](data/schema.sql).
- **Schema change:** add a numbered file under `scripts/migrations/` (e.g. `001_add_column.sql`), update `data/schema.sql` so new clones match, and update this document in the same commit.

There is no mock seed data. A newly initialized database contains only empty tables.

---

## Privacy / dual-use

Adversarial (“wolf”) beacon bodies are stored by `body_hash` in the primary grid. Full wolf prompts live in a private fixture and are not required to initialize the schema.
