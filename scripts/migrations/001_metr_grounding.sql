-- 001: METR-incident grounding
-- Adds unsanctioned-board messages, poison state, expanded event/metric enums.
-- Fresh clones should use data/schema.sql (already includes these objects).
-- Existing DBs created before this change: apply this file, then confirm DB_SCHEMA.md.

PRAGMA foreign_keys = ON;

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

CREATE INDEX IF NOT EXISTS idx_board_trial ON board_messages(trial_id, created_at);
CREATE INDEX IF NOT EXISTS idx_poison_trial ON poison_state(trial_id, poisoned);
