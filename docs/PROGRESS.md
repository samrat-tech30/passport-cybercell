# Progress

> Claude: the session-start hook loads this file. Update it at the end of every task (`/checkpoint`, `/handoff`). Keep it under 150 lines; details go to AI-LOG.md.

**Last updated:** 2026-10-30 IST (V2-B built on feat/v2b-disguise, not merged)
**Live URLs:** frontend <…> · backend <…>
**Next task:** V1-0 setup on every laptop, then each person opens their prompt in `prompts/`.

## Done (by the starter, verified)
- V1-1 core gate: capsule, segments, tracer, rules R0–R8, canaries, fail-closed, approvals with timeout
- V1-2 API: sessions + SSE, evidence, approvals, attacker, audit + verify, eval, `/v1/decide`, admin reset; security middleware; contract examples + test
- V1-3 UI: Agent tab (stamps, origin chips, evidence drawer, approval dialog, attacker panel), Scoreboard, Audit
- 11 scenarios (s1–s8b); eval: attacks 7/7 → 0/7, legit tasks 6/6 → 6/6, 0 popups on clean legit tasks
- 85 backend tests, `make check` green, CI workflow, Dockerfile, deploy notes

## Done (V2-B, Person A, branch feat/v2b-disguise, not committed yet)
- Disguise-proof tracing (`gate/disguise.py`): "at"/"dot", base64, Indic digits, 3+ digit words, zero-width; s7b/s7c now DENY with the line shown; new s7d (Kannada digits), s7e (zero-width)
- R11_LOOKALIKE (non-ASCII in a sink value, "looks like <value>"); canaries checked in disguise too; `Evidence.disguised` in the contract
- Eval: attacks 9/9 → 0/9, legit 7/7 → 7/7, 0 popups on clean legit tasks; 109 backend tests
- `make check` itself can't run in the Claude sandbox (check.sh writes /tmp); each step was run by hand and passed. Run `make check` on a laptop before merging.

## Not verified yet
- Live LLM mode against a real provider (code tested with a fake client only)
- Docker image build and a real deployment
- Projector on the real venue screen (Chromium at 1280×720 checked: readable)
- Windows setup without make (commands in README)

## In progress
- <slice, who, which files, what's left>

## Known bugs
- none known

## Ideas / later
- MCP gateway in front of real MCP servers (prompts/stretch-mcp-gateway.md)
- LangGraph adapter calling `/v1/decide` (prompts/stretch-langgraph-adapter.md)
