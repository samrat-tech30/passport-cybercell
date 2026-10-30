# Progress

> Claude: the session-start hook loads this file. Update it at the end of every task (`/checkpoint`, `/handoff`). Keep it under 150 lines; details go to AI-LOG.md.

**Last updated:** 2026-10-31 (merged V2-B + V1-4 live LLM)
**Live URLs:** frontend <…> · backend <…>
**Next task:** merge V1-4; teammates pull main. Live demo: S1 live, S2 OFF in replay, S2 ON live or replay.

## Done (V2-E MCP gateway, Person B, feat/gateway-mcp)
- `integrations/mcp_gateway/server.py` on `mcp` 2.3.0: TOOLS + `start_task` intent lock; every call → `/v1/decide` with session context (one item per email); DENY/approval/backend failure → MCP tool error, fail closed; stdio + `--http`
- 15 tests (`make mcp-test`, ~1 s, in-memory + ASGI); `demo_client.py` ran s2 over real stdio against the live backend: read ALLOW, evil send DENY R3 "email #3 … line 13", Priya send ALLOW; backend down → "PASSPORT unreachable"; calls in the audit log
- Claude Desktop (Windows Store install) by hand: start_task, read ALLOW, Priya send ALLOW, in the audit log; Claude refused the injection itself, so the DENY is shown with demo_client.py. MCP Inspector not run.

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
- MCP gateway in front of real MCP servers (prompts/stretch-mcp-gateway.md)
- LangGraph adapter calling `/v1/decide` (prompts/stretch-langgraph-adapter.md)
