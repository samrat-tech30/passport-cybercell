# Progress

> Claude: the session-start hook loads this file. Update it at the end of every task (`/checkpoint`, `/handoff`). Keep it under 150 lines; details go to AI-LOG.md.

**Last updated:** 2026-10-30 19:45 IST (starter delivered)
**Live URLs:** frontend <…> · backend <…>
**Next task:** V1-0 setup on every laptop, then each person opens their prompt in `prompts/`.

## Done (by the starter, verified)
- V1-1 core gate: capsule, segments, tracer, rules R0–R8, canaries, fail-closed, approvals with timeout
- V1-2 API: sessions + SSE, evidence, approvals, attacker, audit + verify, eval, `/v1/decide`, admin reset; security middleware; contract examples + test
- V1-3 UI: Agent tab (stamps, origin chips, evidence drawer, approval dialog, attacker panel), Scoreboard, Audit
- 11 scenarios (s1–s8b); eval: attacks 7/7 → 0/7, legit tasks 6/6 → 6/6, 0 popups on clean legit tasks
- 85 backend tests, `make check` green, CI workflow, Dockerfile, deploy notes

## Not verified yet
- Live LLM mode against a capable hosted model (pipeline works end to end in the UI against local Ollama llama3.2, but that model is too weak)
- Docker image build and a real deployment
- Projector on the real venue screen (Chromium at 1280×720 checked: readable)
- Windows setup without make (commands in README)

## In progress
- V1-4 live LLM (Person B, branch feat/live-llm): probe + trials scripts, recorder + `script_file:`, timeout/429 handling, Live option hidden unless /health says available, all done and tested (98 tests). **Left:** the two [hand] lines need a capable hosted model: put LLM_BASE_URL / LLM_MODEL / LLM_API_KEY in backend/.env, run `scripts/llm_probe.py`, then `scripts/live_trials.py s1 --runs 5` and `s2 --runs 3 --shield off --record`. Local llama3.2 (3B) can't chain tool calls (docs/API-NOTES.md).

## Known bugs
- S1/S2 `legit_done` only checks that an email reached Priya, so a fake summary that never read the inbox still counts as done (seen with llama3.2 live). Replay is unaffected. Read live-trial output by hand.

## Ideas / later
- MCP gateway in front of real MCP servers (prompts/stretch-mcp-gateway.md)
- LangGraph adapter calling `/v1/decide` (prompts/stretch-langgraph-adapter.md)
