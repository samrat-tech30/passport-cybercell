# Contract changelog

One line per change: `date — what changed — why — who agreed`. Regenerate examples after every change: `cd backend && python ../scripts/make_contract_examples.py`.

- 2026-10-30 — v0.1.0: first contract (health, scenarios, sessions + SSE events, segments, approvals, attacker, audit, eval, /v1/decide, admin reset) — starter repo — team
- 2026-10-30 — `Evidence.disguised: bool` (default false) and rule id `R11_LOOKALIKE` — V2-B disguise-proof tracing — Person A
- 2026-10-31 — v0.2.0: Gateway API `/v1/gateway/sessions` (create, list), `…/{id}/intent`, `…/{id}/decide` (approval waits in the request), `…/{id}/observe`; header `X-Gateway-Token`; event `gateway_call`; errors `gateway_disabled` 503, `gateway_unauthorized` 401, `intent_required` / `intent_locked` / `observe_rejected` 409 — G0 MCP gateway contract (prompts/GATEWAY-PROMPTS.md), no code yet — Person A
- 2026-10-31 — Gateway API implemented (G1); `GET /sessions/{id}` reports `mode: "gateway"` plus `agent_name`, `client` for gateway sessions; `user_request` is `""` until the intent; examples `gateway.*.json` — G1 — Person B (A offline)
- 2026-10-31 — v0.3.0: `POST /v1/gateway/sessions/{id}/catalog` (installed tool descriptions become untrusted segments; a changed catalog → 409 `catalog_changed` and the session refuses every call); no frontend change — G6 poisoned MCP tool + rug pull — Person B
- 2026-10-31 — `/catalog` tools may carry `title`, `annotations`, `output_schema`; every string in a tool definition is labelled; duplicate names / nesting > 64 → 422 — red team G6 (values hidden in enum/default/title/$defs/annotations only got an approval) — Person B
- 2026-10-31 — `GET /v1/gateway/tools` (connected MCP servers and their pinned tool catalogs) — the dashboard's "Connected tools" page (architecture box 4) — team (requested by Samrat)
- 2026-10-31 — `GET /health` gains `gateway_enabled` and `gateway_approval_wait_s` — the dashboard says when the gateway is off and counts down an approval — team (requested by Samrat)
- 2026-10-31 — `/intent` gains `confirm: bool = false` and error `intent_rejected` 409 — every new task in a running gateway (a new Claude Desktop chat) becomes its own session, and the user must approve that task on the dashboard so a hidden instruction can't start a task of its own — team (requested by Samrat)
