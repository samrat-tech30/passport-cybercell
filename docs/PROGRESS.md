# Progress

> Claude: the session-start hook loads this file. Update it at the end of every task (`/checkpoint`, `/handoff`). Keep it under 150 lines; details go to AI-LOG.md.

**Last updated:** 2026-10-30 22:45 IST (V1-4 live LLM)
**Live URLs:** frontend <…> · backend <…>
**Next task:** projector check of V1-3 polish on the venue screen, then merge feat/ui-polish; merge V1-4; teammates pull main. Live demo: S1 live, S2 OFF in replay, S2 ON live or replay.

## Done (UI round 3: Sky Ink, feat/sky-ink, branched from feat/ui-polish)
- Every screen rebuilt to Sky Ink (docs/DESIGN.md): two-layer tokens, Newsreader headlines, sky hero holding the request + frozen intent + Run, route strip, cards without side borders and with ruled values, origin treatments (yellow highlighter = outside content, black bar = secret), outcome rail, document-style evidence, approval with Reject focused, editorial Scoreboard/Audit, illustrated idle/offline/empty states; dark theme removed
- Checked in Chromium at 1440×900, 1280×720 and 360 wide (no horizontal scroll), S2 on/off, S5 approval + Esc, evidence, scoreboard eval, audit, offline, keyboard order, contrast of every token pair; design/mockups replaced with these screenshots
- Not yet: the real venue projector; merge into main needs the owner's OK

## Done (V1-3 polish, Person B, feat/ui-polish)
- (Look superseded by Sky Ink above) Look: self-hosted Geist/Geist Mono, warm graphite tokens, CSS-only motion (card enter, stamp spring, dialogs, tab plate, count-up), WebGPU guilloché seal in idle state (2D fallback; Chrome on the Core Ultra laptop uses WebGPU)
- Projector 1280×720: left column collapses to a one-line strip; topbar fits one row; step 3 of S2 starts above the fold
- States: backend-down banner + Retry (controls disabled), session error card + Run again, attacker panel says "Nothing received" only after a finished run, run-finished counts, rejected approvals stamped REJECTED + "Agent claimed:"
- Cards: values clamp with "Show full value", sink args loud / subject+body quiet, evidence button pinned right; origin legend; scoreboard sentence from API numbers
- Keyboard: Tab order tabs→controls→timeline, Enter (also on the select) runs, Esc closes evidence / rejects approval (Playwright-checked)
- Fix: dropped SSE stream spun forever (see LESSONS); ui-critic must-fix items done
- Checked in Chromium only, not yet on the real projector

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
