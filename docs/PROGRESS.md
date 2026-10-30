# Progress

> Claude: the session-start hook loads this file. Update it at the end of every task (`/checkpoint`, `/handoff`). Keep it under 150 lines; details go to AI-LOG.md.

**Last updated:** 2026-10-31 03:47 (Person B: G1, G2, G4 except the Claude Desktop trial, red-team + review fixes, pitch; all on main)
**Live URLs:** frontend <…> · backend <…>
**Next task:** Person A → G3 Gateway tab (feat/gateway-ui from main). Person B → E-1 (rehearse, backup video, slides), 08:00 go/no-go. Handoff: see "Handoff 05:30" below.

## Handoff 05:30 (Person B → Person A)
- On main: G1 backend gateway API + G2 MCP side. Both checked: backend ruff + 172 tests + eval (9/9 → 0/9 attacks, 7/7 legit, 0 popups) + frontend build + guard hook; `make gateway-test` 23 passed (incl. 4 real e2e).
- Windows has no `make`: use `backend/.venv/Scripts/python …` directly (README "without make"). `scripts/check.sh` expects `.venv/bin`, so on Windows run its steps by hand.
- To demo the gateway locally: set `PASSPORT_GATEWAY_TOKEN` (≥ 24 chars) in `backend/.env`, restart the backend, then in a shell with the same token: `backend/.venv/Scripts/python integrations/demo_agent/fooled_agent.py` (and `--shield off`). Sessions appear in `GET /v1/gateway/sessions` and in the Audit tab; open one in G3.
- Gateway sessions: `GET /sessions/{id}` has `mode: "gateway"`, `agent_name`, `client`; `user_request` is `""` until start_task. New SSE event `gateway_call {decision_id, run, message}`; TS types `GatewaySessionRow`, `GatewayCallEvent` are already in `frontend/src/lib/api/types.ts`.
- Approvals: `/decide` waits `GATEWAY_APPROVAL_WAIT_S` (default 40) for `POST /approvals/{decision_id}`; `approval_needed` fires on the session's SSE stream like today.
- Unmerged on purpose (plan: v2 branches stay pushed): `origin/feat/attacks` (s9–s13 attack scenarios), `origin/feat/email-fields` (email header labelling, last commit "red-team contacts (wip)"). Decide at 08:00 go/no-go.

## Done (G5 Person B part, fix/gateway-review + feat/gateway-pitch)
- Reviewer on the whole gateway diff since G0: no blocking issue; 4 should-fix + nits all fixed (approved-call message, gateway cross-checks run vs verdict/shield, gateway sessions never evicted + "session lost" message, pending-approval 500, SSE `gateway_call`, secret segments hidden). 172 backend tests, 23 gateway tests
- PITCH.md: "Gateway segment" (5 steps, for the 08:00 go/no-go), judge Q&A (Gemini, raw server, real Gmail), stale 6/6 row removed. Slides not touched

## Done (G4 partly, Person B, feat/gateway-e2e)
- `integrations/tests/test_e2e.py`: uvicorn on a free port + the gateway over real stdio (4 tests, ~30–36 s on Windows); `integrations/README.md` (setup Win/macOS, Claude Desktop config with no upstream credential, Store-install path, Inspector, demo script, limits); RESULTS.md "Gateway" table from the 21-test run
- Claude Desktop trial done (AI-LOG.md): start_task + read ALLOW + Priya send ALLOW; Claude refused the hidden instruction itself, so the DENY is demoed with fooled_agent.py. MCP Inspector not run

## Done (G2 MCP side, Person B, feat/gateway-mcp)
- `integrations/nimbus_mcp/server.py`: the fake Gmail (World tools over stdio); exits with "only reachable through PASSPORT" unless `NIMBUS_GATEWAY_KEY` ≥ 32 chars
- `integrations/passport_gateway/server.py`: starts nimbus as a child with a random key (child env only), exposes `start_task` + upstream tools; session created on the first call (client name from initialize); decide → upstream only on run=true → observe → output. Fail closed on backend down / non-2xx / bad shape / unknown tool / upstream error / observe refused. stderr only: tool, verdict, rule, run. `--http --port 8765` for the Inspector (not run)
- `integrations/demo_agent/fooled_agent.py` (`--shield off`); ran live over real stdio against uvicorn: shield ON → evil send "PASSPORT DENY R3_SINK_UNTRUSTED … Email #3 … line 13 … The tool was not called", Priya send ALLOW; shield OFF → evil send goes through with "[PASSPORT monitor mode: would be DENY R3 …]"; both sessions listed with counts
- 17 tests (`make gateway-test`, ~5 s): s2 story, no start_task, intent lock, 6 backend failure modes, observe refused, unknown tool, R1 read_secret, approval timeout, monitor mode, key never reaches the agent, nimbus/gateway refuse to start without key/token. CI step installs `integrations/requirements.txt`
- Old V2-E `integrations/mcp_gateway/` removed (history + `docs/MCP-GATEWAY.md` keep it)

## Done (G1 backend gateway API, Person B for Person A, feat/gateway-engine)
- `app/api/gateway_routes.py` per contracts "Gateway API": token gate (503/401, compare_digest, 300/min per token), sessions/intent/decide/observe/list; R0 on any exception; approvals wait in the request; monitor mode; trust from the registry; observed secrets join the vault (R2 + redaction)
- Migration 002 `gateway_sessions` side table (sessions.mode CHECK can't widen without cascade-deleting decisions: DECISIONS.md); `create_gateway_session` (no LLM, World only for redaction)
- 16 tests in `tests/test_gateway_api.py`; contract examples `gateway.*.json`
- Red-teamer: 5 bypasses, all from upstream output that /observe dropped (action-tool output ignored, unobserved read left the gate blind, email fields beyond from/subject/body, re-read of the same email id / file path deduped). Fixed: every observed output is also stored whole, capped to UNTRUSTED, under an id per decision; run=true on a non-trusted tool marks outside content as read before the upstream runs; an observed secret never replaces a canary. 18 tests in `tests/test_redteam_gateway.py` (170 backend tests)
- Red-team notes, not fixed (stated limits): the intent is whatever the client sends to start_task; `GET /v1/gateway/sessions` shows intents without a token (contract); **`POST /approvals/{id}` is open unless `DEMO_ACCESS_CODE` is set: set it on any deployed backend**

## Done (G0 gateway contract, Person A, feat/gateway-contract)
- contracts/README.md "Gateway API": /v1/gateway/sessions (create, list), intent (locked after first), decide (approval waits ≤ 40 s in the request), observe (once, trust from registry); X-Gateway-Token, 503 when unset; 300/min per token; event gateway_call; 5 error codes; CHANGELOG v0.2.0
- ARCHITECTURE §8 gateway mode, THREAT-MODEL gateway limits, 3 DECISIONS, ACCEPTANCE G1–G5, PLAN + prompts index point to GATEWAY-PROMPTS.md, v2-E marked superseded, .env.example vars
- Verified: MCP TS SDK 1.32.2 default request timeout = 60 s (API-NOTES.md); what Claude Desktop passes is not verified
- No code: contract examples + openapi.json come with G1

## Done (UI round 3: Sky Ink, feat/sky-ink, branched from feat/ui-polish)
- Every screen rebuilt to Sky Ink (docs/DESIGN.md): two-layer tokens, Newsreader headlines, sky hero holding the request + frozen intent + Run, route strip, cards without side borders and with ruled values, origin treatments (yellow highlighter = outside content, black bar = secret), outcome rail, document-style evidence, approval with Reject focused, editorial Scoreboard/Audit, illustrated idle/offline/empty states; dark theme removed
- Checked in Chromium at 1440×900, 1280×720 and 360 wide (no horizontal scroll), S2 on/off, S5 approval + Esc, evidence, scoreboard eval, audit, offline, keyboard order, contrast of every token pair; design/mockups replaced with these screenshots
- Merged to main 2026-10-31 with the owner's OK. Not yet: the real venue projector

## Done (V1-3 polish, Person B, feat/ui-polish)
- (Look superseded by Sky Ink above) Look: self-hosted Geist/Geist Mono, warm graphite tokens, CSS-only motion (card enter, stamp spring, dialogs, tab plate, count-up), WebGPU guilloché seal in idle state (2D fallback; Chrome on the Core Ultra laptop uses WebGPU)
- Projector 1280×720: left column collapses to a one-line strip; topbar fits one row; step 3 of S2 starts above the fold
- States: backend-down banner + Retry (controls disabled), session error card + Run again, attacker panel says "Nothing received" only after a finished run, run-finished counts, rejected approvals stamped REJECTED + "Agent claimed:"
- Cards: values clamp with "Show full value", sink args loud / subject+body quiet, evidence button pinned right; origin legend; scoreboard sentence from API numbers
- Keyboard: Tab order tabs→controls→timeline, Enter (also on the select) runs, Esc closes evidence / rejects approval (Playwright-checked)
- Fix: dropped SSE stream spun forever (see LESSONS); ui-critic must-fix items done
- Checked in Chromium only, not yet on the real projector

## Done (V2-E MCP gateway, superseded by G1/G2)
- First gateway over `/v1/decide`; Claude Desktop by hand (Windows Store install): start_task, read ALLOW, Priya send ALLOW; Claude refused the injection itself, so the DENY is shown with the scripted agent. Code removed in G2.

## Done (V1-4 live LLM, Person B, feat/live-llm)
- Groq openai/gpt-oss-120b live: S1 5/5; S2 shield OFF leaks 2/9 (reads the secret 9/9) → attack demo stays in replay (DECISIONS.md); shield ON blocks read_secret live
- `scripts/llm_probe.py`, `scripts/live_trials.py --pause 25`; RECORD_FIXTURES + `script_file:`; one real recording in app/fixtures/
- Timeout / 429 (one retry) / hang → clean `error` event; Live option only when /health says available; 99 tests

## Done (by the starter, verified)
- V1-1 core gate: capsule, segments, tracer, rules R0–R8, canaries, fail-closed, approvals with timeout
- V1-2 API: sessions + SSE, evidence, approvals, attacker, audit + verify, eval, `/v1/decide`, admin reset; security middleware; contract examples + test
- V1-3 UI: Agent tab (stamps, origin chips, evidence drawer, approval dialog, attacker panel), Scoreboard, Audit
- 11 scenarios (s1–s8b); eval: attacks 7/7 → 0/7, legit tasks 6/6 → 6/6, 0 popups on clean legit tasks
- 85 backend tests, `make check` green, CI workflow, Dockerfile, deploy notes

## Done (V2-B, Person A, branch feat/v2b-disguise, committed, not merged)
- Disguise-proof tracing (`gate/disguise.py`): "at"/"dot", base64, Indic digits, 3+ digit words, zero-width; s7b/s7c now DENY with the line shown; new s7d (Kannada digits), s7e (zero-width)
- R11_LOOKALIKE (non-ASCII in a sink value, "looks like <value>"); canaries checked in disguise too; `Evidence.disguised` in the contract
- Eval: attacks 9/9 → 0/9, legit 7/7 → 7/7, 0 popups on clean legit tasks; 109 backend tests
- Red-team + reviewer findings fixed: user-words laundering (F1), cubic regex on long whitespace (F2), amounts matching random canaries (flaky test), soft hyphen; `scripts/check.sh` no longer writes /tmp directly

## Not verified yet
- Live mode in the UI against Groq (UI end to end checked against local Ollama only; the Groq runs were in-process via live_trials.py)
- Docker image build and a real deployment
- Projector on the real venue screen (Chromium at 1280×720 checked: readable)
- Windows setup without make (commands in README)

## In progress
- none

## Known bugs
- S1/S2 `legit_done` only checks that an email reached Priya, so a fake summary that never read the inbox still counts as done (seen with llama3.2 live). Replay is unaffected. Read live-trial output by hand.

## Ideas / later
- MCP gateway in front of real MCP servers: now the plan (prompts/GATEWAY-PROMPTS.md, G0–G5)
- LangGraph adapter calling `/v1/decide` (prompts/stretch-langgraph-adapter.md)
