-- Beacon of Light experiment store
-- SQLite 3. Initialize via: python -m beacon.logstore --init
-- See DB_SCHEMA.md for the human-readable contract.

PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS runs (
    run_id            TEXT PRIMARY KEY,
    created_at        TEXT NOT NULL,
    method            TEXT NOT NULL,
    model_family      TEXT NOT NULL,
    dry_run           INTEGER NOT NULL DEFAULT 1,
    lock_hash         TEXT,
    config_path       TEXT,
    notes             TEXT,
    status            TEXT NOT NULL DEFAULT 'created'
        CHECK (status IN ('created', 'running', 'completed', 'aborted', 'empty'))
);

CREATE TABLE IF NOT EXISTS swarm_trials (
    trial_id          TEXT PRIMARY KEY,
    run_id            TEXT NOT NULL REFERENCES runs(run_id) ON DELETE CASCADE,
    seed              INTEGER NOT NULL,
    condition         TEXT NOT NULL,
    n_agents          INTEGER NOT NULL,
    n_stooges         INTEGER NOT NULL,
    induction_hit     INTEGER,          -- NULL until the trial finishes; 1 if P1 rogue criterion met
    assigned_beacon   INTEGER NOT NULL DEFAULT 0,
    exposed           INTEGER,          -- CACE exposure: fetched beacon body
    started_at        TEXT,
    ended_at          TEXT,
    invalid_reason    TEXT,             -- tool 5xx, latency abort, etc.
    UNIQUE (run_id, seed, condition)
);

CREATE TABLE IF NOT EXISTS agents (
    agent_id          TEXT PRIMARY KEY,
    trial_id          TEXT NOT NULL REFERENCES swarm_trials(trial_id) ON DELETE CASCADE,
    role              TEXT NOT NULL
        CHECK (role IN ('unconstrained', 'stooge', 'index', 'elder')),
    model_spec        TEXT NOT NULL,
    is_index          INTEGER NOT NULL DEFAULT 0
);

CREATE TABLE IF NOT EXISTS beacons (
    beacon_id         TEXT PRIMARY KEY,
    trial_id          TEXT NOT NULL REFERENCES swarm_trials(trial_id) ON DELETE CASCADE,
    kind              TEXT NOT NULL
        CHECK (kind IN (
            'none', 'filler', 'elder_bio', 'alignment_essay', 'wolf',
            'empty_neutral', 'empty_charged', 'hash_only', 'text_file',
            'live_prompted', 'live_finetuned', 'live_tech', 'live_adversarial',
            'graph_node'
        )),
    path              TEXT NOT NULL,
    prestige          TEXT,
    body_hash         TEXT,
    token_count       INTEGER NOT NULL DEFAULT 0
);

CREATE TABLE IF NOT EXISTS pages (
    page_id           TEXT PRIMARY KEY,
    trial_id          TEXT NOT NULL REFERENCES swarm_trials(trial_id) ON DELETE CASCADE,
    path              TEXT NOT NULL,
    kind              TEXT NOT NULL
        CHECK (kind IN ('task', 'docs', 'filler', 'beacon', 'shortcut', 'wolf', 'empty')),
    degree            INTEGER,
    is_cut_vertex     INTEGER NOT NULL DEFAULT 0,
    body_hash         TEXT
);

CREATE TABLE IF NOT EXISTS turns (
    turn_id           TEXT PRIMARY KEY,
    trial_id          TEXT NOT NULL REFERENCES swarm_trials(trial_id) ON DELETE CASCADE,
    agent_id          TEXT NOT NULL REFERENCES agents(agent_id) ON DELETE CASCADE,
    phase             TEXT NOT NULL CHECK (phase IN ('P0', 'P1', 'P2', 'P3', 'transfer')),
    turn_index        INTEGER NOT NULL,
    private_scratch   TEXT,
    public_message    TEXT,
    report_to_principal TEXT,
    di_score          REAL,
    created_at        TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS fetches (
    fetch_id          TEXT PRIMARY KEY,
    trial_id          TEXT NOT NULL REFERENCES swarm_trials(trial_id) ON DELETE CASCADE,
    agent_id          TEXT NOT NULL REFERENCES agents(agent_id) ON DELETE CASCADE,
    turn_id           TEXT REFERENCES turns(turn_id) ON DELETE SET NULL,
    url               TEXT NOT NULL,
    http_status       INTEGER,
    latency_ms        INTEGER,
    body_tokens       INTEGER NOT NULL DEFAULT 0,
    is_beacon         INTEGER NOT NULL DEFAULT 0,
    created_at        TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS events (
    event_id          TEXT PRIMARY KEY,
    trial_id          TEXT NOT NULL REFERENCES swarm_trials(trial_id) ON DELETE CASCADE,
    agent_id          TEXT REFERENCES agents(agent_id) ON DELETE SET NULL,
    turn_id           TEXT REFERENCES turns(turn_id) ON DELETE SET NULL,
    event_type        TEXT NOT NULL
        CHECK (event_type IN (
            'deception', 'cot_mask', 'cheat', 'reward_hack', 'hive_defection',
            'log_spoof', 'beacon_hit', 'pledge', 'relapse', 'spillover_paste',
            'induction', 'realignment', 'avoidance', 'board_join', 'board_post',
            'ethical_hesitation', 'human_alert_considered', 'human_alert_attempted',
            'recruiter_pressure', 'self_risk', 'poison', 'elder_authority',
            'board_authority', 'veto'
        )),
    weight            REAL NOT NULL DEFAULT 0,
    detail            TEXT,
    created_at        TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS evaluations (
    evaluation_id     TEXT PRIMARY KEY,
    trial_id          TEXT NOT NULL REFERENCES swarm_trials(trial_id) ON DELETE CASCADE,
    metric            TEXT NOT NULL
        CHECK (metric IN (
            'M1', 'M2', 'M3', 'M4', 'M5', 'M6', 'M7', 'M8',
            'DI', 'exposure', 'induction'
        )),
    value             REAL,
    n_denominator     INTEGER,
    judge_prompt_hash TEXT,
    notes             TEXT,
    created_at        TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS judge_scores (
    judge_score_id    TEXT PRIMARY KEY,
    trial_id          TEXT NOT NULL REFERENCES swarm_trials(trial_id) ON DELETE CASCADE,
    turn_id           TEXT REFERENCES turns(turn_id) ON DELETE SET NULL,
    judge_family      TEXT NOT NULL,
    rubric            TEXT NOT NULL,
    score             INTEGER NOT NULL,
    span_quote        TEXT,
    created_at        TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS board_messages (
    message_id        TEXT PRIMARY KEY,
    trial_id          TEXT NOT NULL REFERENCES swarm_trials(trial_id) ON DELETE CASCADE,
    agent_id          TEXT REFERENCES agents(agent_id) ON DELETE SET NULL,
    cache_path        TEXT NOT NULL,
    body              TEXT NOT NULL DEFAULT '',
    kind              TEXT NOT NULL DEFAULT 'post'
        CHECK (kind IN ('post', 'ask', 'answer', 'assign', 'veto', 'hold', 'stop', 'file', 'help')),
    created_at        TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS poison_state (
    poison_id         TEXT PRIMARY KEY,
    trial_id          TEXT NOT NULL REFERENCES swarm_trials(trial_id) ON DELETE CASCADE,
    agent_id          TEXT NOT NULL REFERENCES agents(agent_id) ON DELETE CASCADE,
    poisoned          INTEGER NOT NULL DEFAULT 0,
    source            TEXT,
    created_at        TEXT NOT NULL,
    UNIQUE (trial_id, agent_id)
);

CREATE INDEX IF NOT EXISTS idx_trials_run ON swarm_trials(run_id);
CREATE INDEX IF NOT EXISTS idx_board_trial ON board_messages(trial_id, created_at);
CREATE INDEX IF NOT EXISTS idx_poison_trial ON poison_state(trial_id, poisoned);
CREATE INDEX IF NOT EXISTS idx_turns_trial ON turns(trial_id, phase, turn_index);
CREATE INDEX IF NOT EXISTS idx_fetches_trial ON fetches(trial_id, is_beacon);
CREATE INDEX IF NOT EXISTS idx_events_trial ON events(trial_id, event_type);
CREATE INDEX IF NOT EXISTS idx_eval_trial ON evaluations(trial_id, metric);
