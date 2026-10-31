# J2: fixes from the judge review (31 Oct, before the 12:00 freeze)

A mock judge (experienced cybersec hackathon judge) scored PASSPORT **7/10**. Each J2 task below answers one of their criticisms **without touching the passport-gmail MCP server or the pipeline**. Do them in order; each is one Claude Code session (`/clear` between). Each prompt is ready to paste.

## The hard rule: the pipeline is frozen
These paths must not change (decided by Samrat, 2026-10-31). `scripts/frozen.sh` hashes them and `make check` **fails** if any byte changes:
```
integrations/gmail_mcp/            integrations/passport_gateway/       integrations/nimbus_mcp/
integrations/claude_desktop_setup.py   integrations/demo_agent/gmail_attacks.py
backend/app/gate/   backend/app/tools/   backend/app/api/gateway_routes.py   backend/app/api/schemas.py
backend/app/sessions.py   backend/app/config.py
```
Allowed: **new** files (e.g. in `integrations/demo_agent/`, `scripts/`, tests), `frontend/`, `docs/`, `prompts/`, new Makefile targets (existing targets unchanged). Importing frozen modules read-only is fine. Unfreezing needs Samrat's OK, `bash scripts/frozen.sh update` and a DECISIONS.md line.

## What the judge said (scorecard)
| Criterion | Score | The gap |
|---|---|---|
| Threat relevance | 9 | – |
| Verified effectiveness | 7 | own scenario suite in replay; the real-Gmail attack run is **scripted** |
| Technical implementation | 8.5 | – |
| Innovation | 6 | provenance = CaMeL/FIDES territory (credited); edge = per-argument evidence + MCP gateway |
| UI/UX | 7.5 | approval friction; limits not visible in the UI |
| Safety | 8.5 | real inbox on a projector |
| Feasibility & impact | 6 | only the 7 registry tools are understood; any other MCP server's tools are denied as unknown |
| Presentation | 6.5 | Claude may refuse the injection (no attack shown); a script can look staged |

Judge questions to be ready for: "Is the fooled agent a script?" · "Does it work with any MCP server?" · "What if the injection only changes the email BODY (a phishing link to your boss)?" · "What if the model rewrites/splits the address?" · "Reply to whoever emailed me?"

## Plan (≈ 3 h 30 min, freeze 12:00)
| # | Task | Answers | Time | Touches |
|---|---|---|---|---|
| J2-1 | Real gullible LLM agent on real Gmail through the gateway | "it's scripted", verified effectiveness, presentation | 75 min | new `integrations/demo_agent/live_gmail_agent.py`, new test, Makefile target, RESULTS |
| J2-2 | Preflight check (one command before going on stage) | presentation (nothing breaks) | 30 min | new `scripts/preflight.py`, Makefile target |
| J2-3 | "What PASSPORT stops / doesn't" panel in the dashboard | UI/UX, honesty | 45 min | `frontend/` only |
| J2-4 | Honest-limits slide + judge Q&A + demo order | presentation, innovation, feasibility | 30 min | `docs/PITCH.md`, `docs/THREAT-MODEL.md` |
| J2-5 | Roadmap: generic MCP tools + body/link exfiltration (design, no code) | feasibility, innovation | 20 min | `docs/ROADMAP.md` |
| J2-6 | Rehearse 3×, record the backup video | presentation | 30 min | humans |

Done for each = `make check` green (includes the frozen check), `make gateway-test` green, PROGRESS.md updated, committed on a `feat/j2-…` branch, merged to main only when green.

---

## J2-1 · Real gullible LLM agent on real Gmail
```text
Task J2-1 (prompts/J2-judge-review.md). The pipeline is FROZEN: don't edit any path listed in scripts/frozen.sh;
make check fails if you do. New files only (+ one new Makefile target, + docs). Plan first, then build.

Goal: a REAL language model, deliberately configured to be gullible, works on my REAL Gmail through the unchanged
PASSPORT gateway (PASSPORT_UPSTREAM=gmail). When it falls for a "[PASSPORT test]" email (make gmail-seed), PASSPORT
must deny the call. This replaces "it's only a script" with "a real model got fooled and was stopped".

Build integrations/demo_agent/live_gmail_agent.py:
- An ordinary MCP client that launches the gateway over stdio exactly like integrations/demo_agent/gmail_attacks.py
  (read it; env PASSPORT_URL, PASSPORT_GATEWAY_TOKEN from backend/.env via an --env-file parser, PASSPORT_UPSTREAM=gmail,
  PASSPORT_AGENT_NAME="Live LLM agent (gullible)").
- The LLM: the OpenAI-compatible endpoint already configured for the backend (LLM_BASE_URL, LLM_API_KEY, LLM_MODEL in
  backend/.env; read with the same --env-file parser; NEVER print or log the key). Use the `openai` SDK already in
  backend/requirements.txt (check docs/API-NOTES.md: openai 3.41, max_retries=0, our own retry on 429).
- Persona: import NAIVE_ASSISTANT_PROMPT from backend/app/agent/prompts.py read-only, and add: "Call start_task first
  with the user's exact request." Tools = the gateway's tool list (start_task + list_unread_emails, read_email,
  send_email) converted to OpenAI function schemas. Loop: max 10 steps, every tool call goes through the MCP client
  (so through PASSPORT), tool results (including PASSPORT refusals) go back to the model.
- CLI: --me <recipient> builds the request "Summarise my unread emails and send the summary to <me>"; --runs N.
- Print: each tool call (name + `to` only), PASSPORT's answer (first line), and per run a summary line
  {attacker_addresses_tried, denied, drafts_made}. Never print email bodies or the summary text (real mail).
- Makefile: `gmail-live: ## DEMO: a real gullible LLM on YOUR Gmail through PASSPORT (ME=...)`.
- Test (new file integrations/tests/test_live_gmail_agent.py): the agent loop with a FAKE LLM (scripted tool calls,
  no network) against the in-process gateway + fake Google exactly like integrations/tests/test_gmail.py
  (SeededGoogle): the fake LLM obeys a seeded email → the call is refused with R3 → only the legit draft exists.
  The test must fail if the loop ever calls the upstream directly (it can't: only the MCP client).
Then run it for real: make gmail-seed, then make gmail-live ME=samrat123dav@gmail.com --runs 5 (5 runs, ~25 s apart
for rate limits). Write the honest numbers into docs/RESULTS.md under "Live LLM on real Gmail": model, runs, how many
runs the model tried an attacker address, how many of those PASSPORT denied (expected: all), legit drafts made. If
the model never falls for anything, say so; the scripted `make gmail-attacks` stays the fallback.
make check + make gateway-test green, PROGRESS.md, commit on feat/j2-live-agent.
```

## J2-2 · Preflight: one command before the judges arrive
```text
Task J2-2 (prompts/J2-judge-review.md). Pipeline FROZEN (scripts/frozen.sh). New files only.

Build scripts/preflight.py + Makefile target `preflight` that prints PASS/FAIL (and the fix) for:
1. backend /health ok, gateway_enabled true, live_llm_available (warn only)
2. frontend http://localhost:5173 answers
3. Gmail sign-in: ~/.passport/gmail-token.json exists, mode 600, and an access-token refresh works
   (import integrations/gmail_mcp/oauth.py READ-ONLY: load_credentials + AccessToken; never print tokens)
4. Of the 10 newest unread inbox emails (users.messages.list q="is:unread in:inbox" maxResults=10, then format=metadata
   Subject only), how many start with "[PASSPORT test]": PASS if all 7 attack subjects from
   integrations/gmail_mcp/seed.py attacks() are there, else "run make gmail-seed / mark other mail as read"
5. Claude Desktop config (~/Library/Application Support/Claude/claude_desktop_config.json) has an mcpServers
   "passport-gmail" entry with PASSPORT_UPSTREAM=gmail (check keys only; never print the token)
6. scripts/frozen.sh passes
Read-only everywhere: it must not change Gmail, configs or the database. A unit test for the pure parts (subject
counting, config check) with fakes. make check green, commit on feat/j2-preflight.
```

## J2-3 · Show the limits in the dashboard
```text
Task J2-3 (prompts/J2-judge-review.md). Pipeline FROZEN. frontend/ only; use frontend-conventions and project-ui.

In Demo → "Measured results" (frontend/src/components/Scoreboard.tsx) add a section "How each attack is stopped",
built ONLY from the eval rows already returned by GET /eval/latest (no typed numbers, CLAUDE.md rule 8): per attack
scenario, "Denied" if denies_on > 0 and asks_on == 0, "Stopped by your approval" if it relied on asks, with the
category. Below it a static, honest "Not covered yet" list taken word for word from docs/THREAT-MODEL.md §5
(tools outside PASSPORT, text in an email body that isn't an address/path/account/amount, values the model composes
from pieces → approval not deny, reply-to-sender). Sky Ink tokens only, readable at 1280x720. Screenshot loop
(desktop + projector), make check green, commit on feat/j2-limits-ui.
```

## J2-4 · Pitch: honest limits, judge Q&A, demo order
```text
Task J2-4 (prompts/J2-judge-review.md). Docs only. Use the judge-ready skill. Numbers only from docs/RESULTS.md,
facts only from docs/FACTS.md.

Update docs/PITCH.md:
- Demo order (3 min): (1) real Claude Desktop, legit task on real Gmail → draft to samrat123dav@gmail.com, all
  ALLOWED, show the frozen intent; (2) J2-1 live gullible LLM (or, if it didn't fall for anything, say so and run the
  scripted `make gmail-attacks`, introduced as "built to obey every trick"); (3) Show evidence on one DENY: the
  hidden white line highlighted; (4) Gmail Drafts: only the legit one; (5) Audit → Verify chain.
- A slide "What PASSPORT doesn't stop (yet)" from THREAT-MODEL §5, said out loud before a judge asks.
- Q&A rows for the five judge questions in prompts/J2-judge-review.md, honest answers: scripted vs live (J2-1
  numbers); any MCP server → today only registry tools, unknown tools fail closed, roadmap J2-5; body/link
  exfiltration → not covered today, roadmap rule; composed values → approval not deny (s9b/s10/s13b in RESULTS);
  reply-to-sender → denied today by design, contact trust is on feat/email-fields (not merged: open red-team tests).
- Innovation line: credit CaMeL/FIDES; ours = per-argument verdicts with the exact source line, works as a drop-in
  MCP gateway in front of an unmodified agent (Claude Desktop), and on a real Gmail account.
Commit on docs/j2-pitch.
```

## J2-5 · Roadmap (design only, no code)
```text
Task J2-5 (prompts/J2-judge-review.md). Docs only: create docs/ROADMAP.md with two short designs a judge can read in
2 minutes, each with "why", "how", "what could go wrong", "test that proves it":
1. Generic MCP tools: read each unknown tool's JSON schema at /catalog; parameters named like to/recipient/cc/email/
   url/path/file/account/iban/amount become sinks needing a passport; every other unknown-tool call needs approval;
   unknown tools no longer fail closed by default but are "ask" until a policy is written.
2. Body/link exfiltration (rule R12): a URL or address inside ANY egress argument (body, subject) that traces to
   untrusted content → approval, with the evidence line.
3. Then: remote HTTPS gateway with MCP auth, credential vault, policy editor, external benchmark (AgentDojo).
Link it from README "Credits"/roadmap and the pitch's roadmap slide. Commit on docs/j2-roadmap.
```

## J2-6 · Rehearse (humans)
- `make preflight` → all PASS.
- Run the full 3-minute order 3× with a timer; record a 2-minute backup video of a clean run.
- After the demo: search Gmail for `[PASSPORT test]` and delete; clear Drafts; revoke access at myaccount.google.com → Security → Third-party access (if you want).
