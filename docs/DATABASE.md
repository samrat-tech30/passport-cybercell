# Database (SQLite)

File: `$DATA_DIR/passport.db` (default `backend/var/passport.db`). WAL mode, foreign keys on, busy timeout 5 s. One connection per process behind a lock (`app/db/database.py`). Only `app/db/` runs SQL.

## Migrations
`app/db/migrations/NNN_name.sql`, applied in filename order at start-up and recorded in `schema_version`. **Never edit an applied migration**: add `002_…sql`. v2 will add `002_threat_ledger.sql`.

## Tables (001_init)
| Table | Purpose | Key columns |
|---|---|---|
| `sessions` | one agent run | id, scenario_id, user_request, shield_on, mode (replay/live), status, capsule_json |
| `decisions` | one gate decision per tool call (args redacted) | id, session_id, step, tool, verdict, rule_id, risk, reasons_json, passports_json, executed, approval |
| `world_events` | what happened in the fake world | session_id, kind (email_sent, attacker_received, payment_made, file_deleted, secret_read), data_json |
| `audit_log` | tamper-evident chain | seq, ts, session_id, kind, payload (canonical JSON), prev_hash, hash |
| `eval_runs` | scoreboard results | id, ts, summary_json, rows_json |

## Audit chain
`hash = SHA-256(prev_hash | ts | session_id | kind | payload)`, genesis = 64 zeros. `GET /audit/verify` walks the chain and reports the first broken row.

Tamper demo (works on every OS, no sqlite3 CLI needed):
```bash
make tamper          # or: cd backend && .venv/bin/python ../scripts/tamper_audit.py
# flips the first DENY in the audit log to ALLOW; press "Verify chain" in the Audit tab -> "Chain broken at row #N"
```
Reset: `make reset-db` (deletes everything including the audit log; only for local testing). `POST /admin/reset` clears sessions and world events but never the audit log.

## Planned (v2)
```sql
-- 002_threat_ledger.sql (v2 upgrade C)
CREATE TABLE IF NOT EXISTS threats (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  kind TEXT NOT NULL CHECK (kind IN ('value','content')),
  fingerprint TEXT NOT NULL,
  first_session TEXT, rule_id TEXT, ts REAL NOT NULL,
  UNIQUE (kind, fingerprint)
);
```
