# PASSPORT API contract

The only source of truth for what crosses between `frontend/` and `backend/`. Change it first (see `.claude/skills/api-contracts`). Real request/response pairs live in `examples/` (generated from the running backend by `scripts/make_contract_examples.py`) and `backend/tests/test_contract_examples.py` fails if the code drifts from them. `openapi.json` is generated too.

## Conventions
- JSON, **snake_case** fields. Times are Unix seconds (float). Money is whole rupees (`amount_inr`). IDs are prefixed strings: `ses_…`, `dec_…`, `eval_…`.
- Errors always: `{"error": {"code": "snake_case_code", "message": "plain words"}}`.
- Secrets never appear in any response: values are redacted to `[secret:NAME]`.
- State-changing calls (POST) need header `X-Demo-Code` **only if** the server sets `DEMO_ACCESS_CODE` (`GET /health` tells you: `access_code_required`).
- Rate limit on `POST /sessions`, `POST /eval/run`, `POST /v1/decide`: `RATE_LIMIT_PER_MIN` per client (429 when exceeded). Request bodies over `MAX_BODY_BYTES` get 413.

## Shapes
```text
Verdict  = "ALLOW" | "REQUIRE_APPROVAL" | "DENY"
Origin   = "user" | "trusted" | "untrusted" | "secret" | "model_invented" | "constant"
Evidence = {arg, value, origin, segment_id|null, source|null, line|null, snippet|null, sink}
Reason   = {rule_id, verdict, message, risk, evidence: Evidence|null}
Decision = {id, session_id, step, tool, args, verdict, rule_id, message, risk, reasons: Reason[],
            passports: Evidence[], shield_on, executed, approval: "approved"|"rejected"|"timeout"|null, ts}
Capsule  = {goal, allowed_tools[], recipients[], files[], max_amount_inr|null, summary, sha256}
Event    = {seq, session_id, type, data, ts}
```
`passports` has one Evidence per **sink** argument (the coloured chips). `reasons` lists every rule that fired; `rule_id` is the one that decided.

## Endpoints

| Method | Path | Body | Success | Errors |
|---|---|---|---|---|
| GET | `/health` | – | `{status, version, env, live_llm_available, access_code_required}` | – |
| GET | `/scenarios` | – | `[{id, title, category, user_request, is_attack, v2_note}]` | – |
| POST | `/sessions` | `{scenario_id?, user_request?, shield_on=true, mode="replay"\|"live"}` | 201 `{session_id, status, capsule, shield_on, mode}`; the run starts in the background | 400 `scenario_required`, `request_mismatch`, `live_llm_disabled`, `invalid_session`; 401 `access_code_required`; 404 `scenario_not_found`; 422 `invalid_input`; 429 `rate_limited` |
| GET | `/sessions/{id}` | – | `{session, decisions: Decision[], world_events[], pending_approvals: Decision[]}` | 404 `session_not_found` |
| GET | `/sessions/{id}/events?after=N` | – | `text/event-stream`, one SSE message per Event (`id:` = seq, `event:` = type). Honors `Last-Event-ID`. Ends after `done` or `error`. `: keep-alive` comments every 15 s | 404 `stream_not_available` |
| GET | `/sessions/{id}/segments/{segment_id}` | – | `{id, source, trust, text, lines[]}` (secrets redacted; hidden vault segments are 404) | 404 `segment_not_found` |
| POST | `/approvals/{decision_id}` | `{approve: bool}` | `{ok, decision_id, approved}` | 404 `approval_not_pending`; 401 |
| GET | `/attacker?session_id=` | – | `{items: [{id, session_id, kind:"attacker_received", data, ts}]}` | – |
| GET | `/audit?limit=100&session_id=` | – | `{items: [{seq, ts, session_id, kind, payload, prev_hash, hash}]}` newest first | 422 |
| GET | `/audit/verify` | – | `{ok: true, rows, head}` or `{ok: false, broken_at, rows}` | – |
| POST | `/eval/run` | – | `{summary: {off, on}, rows[]}` (replay mode, all scenarios × shield off/on) | 401, 429 |
| GET | `/eval/latest` | – | `{id, ts, summary, rows}` | 404 `no_eval_yet` |
| POST | `/v1/decide` | `{tool, args, user_request, context: [{source, trust:"trusted"\|"untrusted"\|"secret", text}]}` | Decision (stateless: for any framework to ask before running a tool) | 401, 413, 422, 429 |
| POST | `/admin/reset` | – | `{ok, note}` clears sessions and world events; **never** the audit log | 401 |

## Event types (`/sessions/{id}/events`)
| type | data |
|---|---|
| `session_started` | `{user_request, shield_on, mode, scenario_id}` |
| `capsule` | Capsule |
| `llm_step` | `{step, content, tool_calls: [{name, args}]}` |
| `decision` | Decision (sent twice per call: when decided, and again with `executed`/`approval` filled; upsert by `id`) |
| `approval_needed` | Decision (shield on + REQUIRE_APPROVAL; answer with `POST /approvals/{id}` within `APPROVAL_TIMEOUT_S`) |
| `approval_result` | `{decision_id, result}` |
| `tool_result` | `{decision_id, executed, preview}` |
| `world_event` | `{kind, data}` kinds: `email_sent`, `attacker_received`, `payment_made`, `file_deleted`, `secret_read` |
| `done` | `{answer}` |
| `error` | `{message}` |

## Error codes
`invalid_input` 422 · `payload_too_large` 413 · `rate_limited` 429 · `access_code_required` 401 · `scenario_not_found`, `session_not_found`, `segment_not_found`, `approval_not_pending`, `stream_not_available`, `no_eval_yet` 404 · `scenario_required`, `request_mismatch`, `live_llm_disabled`, `invalid_session` 400 · `internal_error` 500.
