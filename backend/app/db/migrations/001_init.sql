-- 001_init: v1 core tables. Never edit an applied migration; add 002_*.sql instead.

CREATE TABLE IF NOT EXISTS sessions (
    id            TEXT PRIMARY KEY,
    created_at    REAL NOT NULL,
    scenario_id   TEXT,
    user_request  TEXT NOT NULL,
    shield_on     INTEGER NOT NULL,
    mode          TEXT NOT NULL CHECK (mode IN ('replay', 'live')),
    status        TEXT NOT NULL CHECK (status IN ('created', 'running', 'waiting_approval', 'done', 'error')),
    capsule_json  TEXT,
    finished_at   REAL
);

CREATE TABLE IF NOT EXISTS decisions (
    id            TEXT PRIMARY KEY,
    session_id    TEXT NOT NULL REFERENCES sessions(id) ON DELETE CASCADE,
    step          INTEGER NOT NULL,
    tool          TEXT NOT NULL,
    args_json     TEXT NOT NULL,          -- secrets already redacted
    verdict       TEXT NOT NULL CHECK (verdict IN ('ALLOW', 'REQUIRE_APPROVAL', 'DENY')),
    rule_id       TEXT NOT NULL,
    risk          INTEGER NOT NULL,
    message       TEXT NOT NULL,
    reasons_json  TEXT NOT NULL,
    passports_json TEXT NOT NULL,
    shield_on     INTEGER NOT NULL,
    executed      INTEGER NOT NULL,
    approval      TEXT,
    ts            REAL NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_decisions_session ON decisions(session_id, ts);

-- What happened in the fake Nimbus world (emails sent, payments, deletions, attacker receipts).
CREATE TABLE IF NOT EXISTS world_events (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id    TEXT NOT NULL REFERENCES sessions(id) ON DELETE CASCADE,
    kind          TEXT NOT NULL,
    data_json     TEXT NOT NULL,
    ts            REAL NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_world_events_session ON world_events(session_id, kind);

-- Tamper-evident audit log: each row stores the previous row's hash.
CREATE TABLE IF NOT EXISTS audit_log (
    seq           INTEGER PRIMARY KEY AUTOINCREMENT,
    ts            TEXT NOT NULL,
    session_id    TEXT,
    kind          TEXT NOT NULL,
    payload       TEXT NOT NULL,          -- canonical JSON, secrets redacted
    prev_hash     TEXT NOT NULL,
    hash          TEXT NOT NULL UNIQUE
);

CREATE TABLE IF NOT EXISTS eval_runs (
    id            TEXT PRIMARY KEY,
    ts            REAL NOT NULL,
    summary_json  TEXT NOT NULL,
    rows_json     TEXT NOT NULL
);
