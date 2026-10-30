# Contract changelog

One line per change: `date — what changed — why — who agreed`. Regenerate examples after every change: `cd backend && python ../scripts/make_contract_examples.py`.

- 2026-10-30 — v0.1.0: first contract (health, scenarios, sessions + SSE events, segments, approvals, attacker, audit, eval, /v1/decide, admin reset) — starter repo — team
- 2026-10-30 — `Evidence.disguised: bool` (default false) and rule id `R11_LOOKALIKE` — V2-B disguise-proof tracing — Person A
- 2026-10-31 — v0.2.0: Gateway API `/v1/gateway/sessions` (create, list), `…/{id}/intent`, `…/{id}/decide` (approval waits in the request), `…/{id}/observe`; header `X-Gateway-Token`; event `gateway_call`; errors `gateway_disabled` 503, `gateway_unauthorized` 401, `intent_required` / `intent_locked` / `observe_rejected` 409 — G0 MCP gateway contract (prompts/GATEWAY-PROMPTS.md), no code yet — Person A
- 2026-10-31 — Gateway API implemented (G1); `GET /sessions/{id}` reports `mode: "gateway"` plus `agent_name`, `client` for gateway sessions; `user_request` is `""` until the intent; examples `gateway.*.json` — G1 — Person B (A offline)
