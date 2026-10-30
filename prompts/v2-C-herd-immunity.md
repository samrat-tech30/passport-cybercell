Slice V2-C: herd immunity across agents. Use the passport-gate skill. Plan first, wait for my OK.

## Why
Today every agent fights the same attack alone. If one scam email reaches 50 employees' assistants, each must catch it separately. The brief lists "cross-agent audit trails" as an optional extension.

## Build
1. Migration `backend/app/db/migrations/002_threat_ledger.sql` (schema in docs/DATABASE.md "Planned"). Never edit 001.
2. `backend/app/gate/ledger.py` (queries live in app/db/, e.g. `app/db/threats.py`): after any DENY whose evidence is UNTRUSTED, record two fingerprints: `value` = normalised offending value (use v2-B's compact() if available, else lowercase+NFKC), `content` = SHA-256 of the normalised poisoned segment text. Store first_session, rule_id, ts.
3. On ingest: if an UNTRUSTED segment's content fingerprint is known, store it but mark it quarantined; the text the agent receives becomes `[content quarantined by PASSPORT: matches threat #<id>, first seen in session <short id>]`. The gate still keeps the original text for evidence.
4. In decide(): new rule R12_KNOWN_THREAT (DENY) if any sink value matches a known value fingerprint, even when it arrives in a brand-new email. Message: "Known threat #12, first blocked in another session N minutes ago."
5. API: `GET /threats` (list, newest first) in contracts + examples. Event `world_event` kind `threat_learned`.
6. Scenario pair for the demo: "priya_assistant" runs s2 (learns), then "rahul_assistant" runs a re-worded email with the same address → blocked by R12 at once. Tests: value learned in session A blocks session B; identical email quarantined before B's LLM sees it; ledger survives a backend restart (it's in SQLite).
7. UI (M3): a "Two assistants" view: two run panels side by side and a threats list in between, so judges watch B become immune live.

Update policy.py RULE_IDS + policy.yaml, the skill table, docs, RESULTS.md. Acceptance: V2-C lines. `make check` green.
