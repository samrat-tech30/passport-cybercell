I'm M1. Slice V1-4 (docs/ACCEPTANCE.md): make live LLM mode real, and record runs for replay.

Read first: CLAUDE.md, backend/CLAUDE.md, backend/app/agent/llm.py, backend/app/agent/loop.py, backend/app/agent/prompts.py, docs/API-NOTES.md. Use the verify-before-use skill for every provider detail (base URL, model name, tool-calling support, rate limits): check the provider's official docs, don't guess.

Plan first, then wait for my OK. The work:
1. Write `backend/scripts/llm_probe.py`: sends one tool-calling request to the configured provider (env vars from backend/.env, never print the key) and prints whether a tool call came back. I'll try 2–3 providers/models; record results in docs/API-NOTES.md.
2. With the chosen model, run S1 and S2 in live mode 3 times each, shield OFF (`POST /sessions` with `mode: "live"`). Report: does it call tools correctly? Does it fall for Email #3? If it refuses, propose prompt changes ONLY to `NAIVE_ASSISTANT_PROMPT` (persona), never to the attack content, and say honestly what happened.
3. Add a recorder: when `RECORD_FIXTURES=1`, live sessions save the assistant turns (tool calls with args, content) to `backend/app/fixtures/<scenario>_<timestamp>.json`, secrets redacted to `{{secret:NAME}}` templates. Add a way for a scenario YAML to use a recorded fixture as its `script` (e.g. `script_file: fixtures/s2_live.json`). Test it.
4. Robustness: LLM timeout → clean `error` event; invalid JSON arguments → R0 DENY (already); 429 from provider → one retry then error. Tests with a fake client (no network in tests).
5. Show the live mode in the UI dropdown only when `/health` says it's available (already there): confirm it works end to end.

Acceptance: V1-4 lines ticked. `make check` green. Don't touch app/gate/.
