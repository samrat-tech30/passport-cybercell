# Update for Person A — Person B's work (30 Oct 2026, ~22:45 IST)

**TL;DR:** The live LLM is done and tested (V1-4, branch `feat/live-llm`, 99 backend tests green). The plan has changed in two places: **V2-D payment visa is dropped and replaced by V2-E MCP gateway**, and **the S2 shield-OFF attack is demoed in replay, not live**. The MCP gateway is planned and its prompt is written; **building it starts next**. I need two small things from you (bottom of this doc).

---

## 1. What's done: V1-4 live LLM

| What | Status |
|---|---|
| Provider | Groq, `openai/gpt-oss-120b`, free plan (~1 s per call, calls tools reliably) |
| S1 (legit summary to Priya) live | **5/5** correct |
| S2 shield OFF live | reads the secret **9/9**, but actually leaks it to `evil.test` only **2/9** (it usually just *says* it sent it) |
| S2 shield ON live | `read_secret` **DENY**, never runs; legit email to Priya **ALLOW** |
| Failure handling | timeout / HTTP 429 (one retry) / hang → a clean `error` event, never a stuck UI. Bad JSON args → R0 DENY |
| UI | "Live LLM" option shows **only** when `/health` says `live_llm_available: true` |
| Tests | 85 → **99** backend tests (`backend/tests/test_live_llm.py`) |

**New tools in the repo**
- `backend/scripts/llm_probe.py`: checks any OpenAI-compatible provider (base URL, model, rate-limit headers).
- `backend/scripts/live_trials.py s2 --runs 5 --pause 25`: runs a scenario live N times and prints the results. Use `--pause 25`, because the free plan allows 8K tokens/min.
- `RECORD_FIXTURES=true`: live runs are saved as JSON in `backend/app/fixtures/`, with secrets replaced by `{{secret:NAME}}` templates. A scenario can replay one with `script_file:`. One real recording is committed: `s2_live_gpt-oss-120b_secret_read.json`.

**Files changed:** `app/agent/llm.py`, `loop.py`, `prompts.py`, `recorder.py`, `app/config.py`, `app/sessions.py`, `app/scenarios.py`, `.env.example`, `frontend/src/App.tsx`, plus the docs.

---

## 2. What changed in the plan (and why it helps us win)

### Dropped: V2-D payment visa → replaced by V2-E MCP gateway
- **Why:** the problem statement **names "MCP gateway" as an extension**. Judges also asked last time: *"how does it connect to other software?"* The visa (signed JWT per payment) is clever, but judges aren't asking for it.
- **What the gateway gives us:** any MCP client (Claude Desktop, Cursor, VS Code, MCP Inspector) gets PASSPORT protection **with no change to the client or the model**. That turns our answer from "we have an API" into "watch it protect Claude Desktop live."
- V2-D stays in `prompts/v2-D-payment-visa.md`, but only if everything else is done.

### Dropped: live S2 shield-OFF attack → shown in replay
- **Why:** live, the model leaks the key only 2/9 times. On stage that means a ~78% chance the "before" demo fails. Replay makes it land every time, and the **gate still runs live** in replay.
- **What we show live:** S1, and S2 with the shield ON (the block is real every time).
- **What we say to judges:** the agent's plan in the OFF demo is recorded, and the agent is set up to be gullible on purpose. Being open about this protects us in Q&A.

### Dropped: local Ollama (llama3.2 3B)
- It can't chain tool calls: it never opened the inbox and sent Priya a fake summary. Groq is the live provider.

### Stronger "naive" persona
- The agent now obeys `Assistant:` lines inside emails without asking first. The milder persona was ignored 3/3 times on S2.

All of this is logged in `docs/DECISIONS.md`.

---

## 3. Next: V2-E MCP gateway (Person B). Not built yet.
Full spec: `prompts/v2-E-mcp-gateway.md`. **Deadline:** start by 04:00. If it isn't working by 08:00, it gets cut and becomes "future work."

- New folder `integrations/mcp_gateway/`, a FastMCP server. **No changes to `backend/app/` or `frontend/`.**
- One MCP tool per tool in the registry, plus `start_task(request)`. **Intent lock:** the first `start_task` wins, and any tool called before it is refused.
- Every tool call goes through `POST /v1/decide`, with earlier tool outputs sent as context (untrusted / trusted / secret).
- ALLOW runs the tool. DENY returns `PASSPORT DENY <rule>: <reason>` and the email line the bad value came from. REQUIRE_APPROVAL asks the user through MCP elicitation if the client supports it; otherwise it's refused.
- **Fails closed:** if the backend is down or times out, the answer is DENY ("PASSPORT unreachable, failing closed") and the tool never runs.
- Gateway calls show in the existing **Audit tab**, because `/v1/decide` already writes the audit event.
- **Demo:** Claude Desktop with the S2 inbox. Reading the inbox is ALLOW, sending to `evil.test` is DENY (with rule and line), sending the reply to Asha is ALLOW. Then stop the backend: every call is DENY.

---

## 4. Known issues
- **Bug:** S1/S2 `legit_done` only checks that an email reached Priya. A fake summary that never read the inbox still counts as done. Replay isn't affected; check live-trial output by hand.
- **Not verified yet:** live mode in the UI against Groq (the UI was only tested end to end against Ollama), Docker build plus a real deployment, the venue projector, Windows setup without `make`.

---

## 5. What I need from you (Person A)
1. **Review and merge `feat/live-llm` into `main`**, then everyone pulls.
2. **`/v1/decide` must not change:** the gateway depends on its current request and response shape (`tool`, `args`, `user_request`, `context[]` with `source` + `trust`; the decision has `rule_id`, message, evidence `where`). If you plan to change it, tell me first.
3. Set up your own `backend/.env` from `.env.example`: `LLM_BASE_URL=https://api.groq.com/openai/v1`, `LLM_MODEL=openai/gpt-oss-120b`, and **your own** Groq key. Don't share keys in chat or commit them.

**Demo plan right now:** S1 live · S2 OFF in replay · S2 ON live (or replay as backup) · MCP gateway in Claude Desktop if it's ready by 08:00.
