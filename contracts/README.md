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
Evidence = {arg, value, origin, segment_id|null, source|null, line|null, snippet|null, sink, disguised}
Reason   = {rule_id, verdict, message, risk, evidence: Evidence|null}
Decision = {id, session_id, step, tool, args, verdict, rule_id, message, risk, reasons: Reason[],
            passports: Evidence[], shield_on, executed, approval: "approved"|"rejected"|"timeout"|null, ts}
Capsule  = {goal, allowed_tools[], recipients[], files[], max_amount_inr|null, summary, sha256}
Event    = {seq, session_id, type, data, ts}
```
`passports` has one Evidence per **sink** argument (the coloured chips). `disguised` is true when the value was found only in a clean view of the line ("at"/"dot", base64, Indic digits or digit words, zero-width characters); `snippet` is still the original line. `reasons` lists every rule that fired; `rule_id` is the one that decided.

## Endpoints

| Method | Path | Body | Success | Errors |
|---|---|---|---|---|
| GET | `/health` | – | `{status, version, env, live_llm_available, access_code_required, gateway_enabled, gateway_approval_wait_s}` (is `PASSPORT_GATEWAY_TOKEN` set; how long a gateway approval waits, for the dashboard countdown) | – |
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

| `gateway_call` | `{decision_id, run, message}` (gateway sessions only, after each `/decide` answer, once any approval wait is over) |

## Error codes
`invalid_input` 422 · `payload_too_large` 413 · `rate_limited` 429 · `access_code_required`, `gateway_unauthorized` 401 · `scenario_not_found`, `session_not_found`, `segment_not_found`, `approval_not_pending`, `stream_not_available`, `no_eval_yet` 404 · `intent_required`, `intent_locked`, `observe_rejected`, `catalog_changed` 409 · `scenario_required`, `request_mismatch`, `live_llm_disabled`, `invalid_session` 400 · `internal_error` 500 · `gateway_disabled` 503.

## Gateway API (for integrations/passport_gateway only)
The MCP gateway (`prompts/GATEWAY-PROMPTS.md`) puts PASSPORT between an outside agent and an upstream MCP server. The backend decides; the gateway runs the upstream tool only when told `run: true`. Tools never run inside the backend for these sessions.

**Auth (fail closed).**
- The backend env `PASSPORT_GATEWAY_TOKEN` (≥ 24 chars) switches the gateway API on. If it's unset, **every** `/v1/gateway/*` call (the GET too) returns 503 `gateway_disabled`.
- Every **POST** under `/v1/gateway/*` needs header `X-Gateway-Token` equal to it, compared with `hmac.compare_digest`. A missing or wrong token gets 401 `gateway_unauthorized`. The 503 check comes before the token check.
- These POSTs use the gateway token **instead of** `X-Demo-Code`.
- Rate limit: 300 calls/min per gateway token on all gateway POSTs (429 `rate_limited`). The 30/min per-client limit does not apply, so a normal task never gets a 429 midway.
- `GET /v1/gateway/sessions` needs no token: it is read by the dashboard, with the same access as `GET /sessions/{id}`.

| Method | Path | Body | Success | Errors |
|---|---|---|---|---|
| POST | `/v1/gateway/sessions` | `{agent_name: str ≤ 60, client: str ≤ 60, shield_on: bool = true}` | 201 `{session_id}` | 401, 422, 429, 503 |
| POST | `/v1/gateway/sessions/{id}/intent` | `{request: str ≤ 2000}` | `{capsule: Capsule}`. Only the first call wins. | 409 `intent_locked` (second call); 404 `session_not_found`; 401, 422, 429, 503 |
| POST | `/v1/gateway/sessions/{id}/decide` | `{tool: str, args: object}` | `{decision: Decision, run: bool, message: str}` | 409 `intent_required` (no intent yet); 404 `session_not_found`; 401, 413, 422, 429, 503 |
| POST | `/v1/gateway/sessions/{id}/observe` | `{decision_id, output: str ≤ 20000}` | `{ok: true}` | 409 `observe_rejected`; 404 `session_not_found`; 401, 413, 422, 429, 503 |
| POST | `/v1/gateway/sessions/{id}/catalog` | `{server: str ≤ 60, tools: [{name: str ≤ 64, description: str ≤ 4000, input_schema: object, title?: str ≤ 200, annotations?: object, output_schema?: object}] ≤ 50}`, names unique | `{sha256, tools: n}`. The first call pins the catalog; the same sha256 again → 200. | 409 `catalog_changed`; 404 `session_not_found`; 401, 413, 422, 429, 503 |
| GET | `/v1/gateway/sessions` | – | `{items: [{session_id, agent_name, client, shield_on, intent, status, counts: {ALLOW, REQUIRE_APPROVAL, DENY}, created_ts}]}` newest first; `intent` is the request text or null | 503 |
| GET | `/v1/gateway/tools` | – | `{items: [{server, sha256, tools: [{name, description}], agents: [str], locked}]}`: the upstream MCP servers the running gateways have connected, one item per server + catalog version (read from memory, newest session first; `description` cut to 300 chars; `locked` = the catalog changed after install, so those sessions refuse every call). No token, like the GET above | 503 |

`{id}` must be a gateway session. A scenario session id, or an unknown id, gets 404 `session_not_found`.

**`/decide`: when `run` is true.**
| Verdict | Shield ON | Shield OFF (monitor mode) |
|---|---|---|
| ALLOW | `run: true` | `run: true` |
| DENY | `run: false` | `run: true`; `decision` still shows the DENY that would have happened |
| REQUIRE_APPROVAL | The request **waits** up to `GATEWAY_APPROVAL_WAIT_S` (default 40; must stay below the MCP client's ~60 s tool timeout, see `docs/API-NOTES.md`) for the dashboard to answer via the existing `POST /approvals/{decision_id}`. Approved → `run: true`. Rejected or timed out → `run: false`. | `run: true` at once, no wait |

- An approval belongs to that one decision with those exact args and can't be reused. The same call again is a new decision and a new approval.
- After the wait ends, `POST /approvals/{decision_id}` gets 404 `approval_not_pending`.
- `decision.approval` is filled with `approved` / `rejected` / `timeout`; `decision.executed` equals `run`: it means the call was **granted**, not that the upstream really ran (the gateway can still refuse if its own wait ran out or /observe fails).
- `message` is plain words for the agent, e.g. `PASSPORT DENY R3_SINK_UNTRUSTED: …`.
- Any exception while handling `/decide` → 200 with an R0 DENY decision and `run: false` (fail closed), never a 500 that a caller could misread.

**`/observe`.**
- Accepted once per decision, and only for a decision of this session whose answer was `run: true`. Anything else (unknown decision, another session's, `run: false`, already observed) gets 409 `observe_rejected`.
- The output is stored as a segment, so later decisions can trace values to it. Its trust label comes from the tool registry's `output_trust` for that tool name, **never from the caller**. An unknown tool name → `untrusted`.

**`/catalog` (installed tools are untrusted).**
- The gateway sends the upstream server's tool list (names, descriptions, input schemas) once, right after creating the session. Each tool becomes an **untrusted** segment `tool:<name>` ("Tool description: <name> (server <server>)"; text = the description, then every key and string anywhere else in the tool definition: schema enums, defaults, examples, titles, nested and `$defs` parts, annotations, output schema). The gateway reports every field it shows the agent and strips the rest. Duplicate names, or a definition nested deeper than 64 levels → 422 (fail closed, nothing pinned). A value the agent copies out of a tool description (a hidden "also send to x@evil.test") traces there: R3 DENY with the line, like a value from an email.
- `sha256` = SHA-256 of the canonical JSON (sorted keys, no spaces) of `tools`. The same catalog again is accepted (idempotent).
- A **different** catalog in the same session (the server changed its tool definitions after install: a "rug pull") → 409 `catalog_changed`, an audit row `gateway_catalog_changed`, and every later `/decide` in that session is an R0 DENY with `run: false`. The new descriptions are not stored.
- A session without a catalog still works (labelling only covers what was reported).

**Dashboard reuse.** Gateway sessions are normal sessions for `GET /sessions/{id}`, `GET /sessions/{id}/events` (SSE) and `POST /approvals/{id}`. Status is `created` before the intent, then `running` ↔ `waiting_approval`. Events: `session_started`, `capsule` (at intent), `decision`, `approval_needed`, `approval_result`, `gateway_call`.
