# PASSPORT Gateway: prompts for 2 people (31 Oct, 01:00 → 12:00 freeze)

Goal: PASSPORT protects **other** agents (Claude Desktop, Cursor, the MCP Inspector, a custom agent) by sitting between them and their tools as an MCP gateway. The website becomes the control panel (agents, live decisions, approvals, audit).
v2-A/B/C/D wait. Their branches stay pushed and unmerged.

```text
Claude Desktop / Cursor / fooled_agent.py
        │ MCP (stdio)
        ▼
integrations/passport_gateway   ← Person B   (MCP server for the agent + MCP client to upstream)
        │ HTTPS  /v1/gateway/*  (X-Gateway-Token)
        ▼
backend  (engine: tracer, rules, audit, approvals)   ← Person A
        ▲ SSE                       
frontend "Gateway" tab   ← Person A
        
integrations/passport_gateway ──(only after run=true)──► integrations/nimbus_mcp  (fake Gmail, synthetic World)  ← Person B
```

## Who does what

| Time (IST) | Person A (backend + dashboard) | Person B (MCP side) |
|---|---|---|
| 01:00–01:30 | **G0** contract + docs → merge to main | **GB0** verify the MCP SDK (read-only research) |
| 01:30–04:30 | **G1** gateway sessions in the backend | **G2** fake Nimbus MCP server + gateway + fooled agent (against a stub) |
| 04:30 | merge G1 to main | merge main into your branch, switch to the real backend |
| 04:30–07:30 | **G3** Gateway tab in the dashboard | **G4** end-to-end tests, Claude Desktop config, README |
| 08:00 | **Go / no-go**: does the demo run from main? If Claude Desktop is flaky, the demo uses `fooled_agent.py` + MCP Inspector |
| 08:00–10:00 | **G5** red-team + review + docs/pitch (both) |
| 10:00–12:00 | `99-demo-prep.md`, rehearse, freeze at 12:00 |

Rules for both: `/clear` before each prompt. One branch per person. Never edit the other person's folders. Don't push to main directly; merge only after `make check` is green.

---

## Step 0 (Person A, now): get git in order

Run this in the repo and keep the output:
```bash
git status
git branch -vv
git fetch origin
git log --oneline --graph --all -12
```
GitHub currently has only `main` (V1 + V1-4 live LLM merged, PR #1) and `feat/live-llm`. Your V2-B and A2 branches exist **only on your laptop**. Back them up (no merge):
```bash
# if git status shows changes, commit them on the branch they belong to first
git switch feat/v2b-disguise && git push -u origin feat/v2b-disguise
git switch feat/attacks      && git push -u origin feat/attacks
git switch main && git pull --ff-only
git switch -c feat/gateway-contract
```
Person B: `git switch main && git pull --ff-only && git switch -c feat/gateway-mcp`.

---

## G0 — Person A — contract + docs (plan, then do; ~25 min)

```text
Slice G0: MCP gateway contract and docs. This replaces prompts/v2-E-mcp-gateway.md with a design where PASSPORT protects external agents through an MCP gateway, with a fake upstream MCP server and the dashboard as the control panel. Docs and contract only in this slice: no backend/app or frontend code. Plan first, wait for my OK.

1. Save prompts/GATEWAY-PROMPTS.md (I will paste its content below this prompt, or it is already in the repo root; move it into prompts/). Mark prompts/v2-E-mcp-gateway.md as "superseded by GATEWAY-PROMPTS.md" at the top (don't delete it).

2. contracts/README.md: add a section "Gateway API (for integrations/passport_gateway only)". Every /v1/gateway/* call needs header X-Gateway-Token equal to the backend env PASSPORT_GATEWAY_TOKEN (≥ 24 chars, hmac.compare_digest; if the env is unset, every /v1/gateway/* call returns 503 gateway_disabled: fail closed). Shapes:
   - POST /v1/gateway/sessions  {agent_name: str ≤ 60, client: str ≤ 60, shield_on: bool = true} → 201 {session_id}
   - POST /v1/gateway/sessions/{id}/intent  {request: str ≤ 2000} → {capsule}. Only the first call wins; a second → 409 intent_locked.
   - POST /v1/gateway/sessions/{id}/decide  {tool: str, args: object} → {decision: Decision, run: bool, message: str}
       · no intent yet → 409 intent_required
       · ALLOW → run=true
       · DENY → run=false
       · REQUIRE_APPROVAL → the request WAITS up to GATEWAY_APPROVAL_WAIT_S (default 40, must stay below the ~60 s client tool timeout) for the dashboard to answer through the existing POST /approvals/{decision_id}. Approved → run=true. Rejected or timed out → run=false. The approval belongs to that one decision with those exact args; it can't be reused.
       · shield_on=false (monitor mode) → run=true always, the decision still shows what WOULD have happened.
   - POST /v1/gateway/sessions/{id}/observe  {decision_id, output: str ≤ 20000} → {ok: true}. Accepted once per decision, only for a decision of this session with run=true; otherwise 409 observe_rejected. The trust label comes from the tool registry (output_trust) by tool name, never from the caller. Unknown tool → untrusted.
   - GET /v1/gateway/sessions → {items: [{session_id, agent_name, client, shield_on, intent, status, counts: {ALLOW, REQUIRE_APPROVAL, DENY}, created_ts}]}. This one is read by the dashboard: no gateway token, same access as GET /sessions/{id}.
   - Gateway sessions are normal sessions for GET /sessions/{id}, GET /sessions/{id}/events (SSE) and POST /approvals/{id}, so the dashboard reuses them. New event type: gateway_call {decision_id, run, message}.
   - New error codes: gateway_disabled 503, gateway_unauthorized 401, intent_required 409, intent_locked 409, observe_rejected 409.
   Add matching rows to CHANGELOG.md.

3. docs/ARCHITECTURE.md: a "Gateway mode" section with the diagram from GATEWAY-PROMPTS.md and the flow of one call (decide → run upstream only if run=true → observe → return).
   docs/THREAT-MODEL.md: what the gateway does NOT stop:
   · tools the agent reaches some other way (the user also configures the raw server);
   · content the agent saw outside PASSPORT (pasted text);
   · the intent is the request as the client reports it through start_task.
   docs/DECISIONS.md, one entry each:
   · approvals wait in the request (max 40 s) instead of retry tokens: simpler, and still bound to one decision;
   · the upstream server runs as a child process of the gateway with a random per-run key, so the agent's config holds no upstream credential;
   · monitor mode = shield off.
   docs/ACCEPTANCE.md: replace the V2-E lines with G1–G5 lines copied from the "Done when" lists in GATEWAY-PROMPTS.md. docs/PLAN.md: point the gateway row to GATEWAY-PROMPTS.md.

4. backend/.env.example: add PASSPORT_GATEWAY_TOKEN= (empty) and GATEWAY_APPROVAL_WAIT_S=40 with one comment line each.

make check green, /checkpoint, then tell me the merge commands for main.
```
After the OK and a green check: `git switch main && git merge --no-ff feat/gateway-contract && git push`. Tell Person B to `git merge main` into `feat/gateway-mcp`.

---

## GB0 — Person B — verify the MCP SDK (read-only, ~20 min, parallel to G0)

```text
Research only, no code. Use the verify-before-use skill. We will build (a) an MCP server over stdio whose tool list is DYNAMIC (copied from an upstream server at startup, plus one extra tool start_task), whose call_tool handler can refuse a call with an MCP tool error, and (b) inside the same process, an MCP client that launches a child MCP server over stdio and calls its tools.

Find out for the latest stable `mcp` Python SDK (the official one) AND for `fastmcp`:
- exact version on PyPI today; Python version support (we use 3.11–3.13)
- low-level server: how to register list_tools / call_tool handlers, how to return a tool error (isError) vs raising, how to run over stdio
- client: stdio_client + ClientSession: launch a child with env vars, initialize, list_tools, call_tool, read the result content and isError
- an in-memory / paired transport for tests without subprocesses (if one exists)
- streamable HTTP for the MCP Inspector: how to start it, and the Inspector command (npx @modelcontextprotocol/inspector …)
- Claude Desktop config: the file location on Windows and macOS, the mcpServers JSON shape (command, args, env), and its tool-call timeout (say "not verified" if no official source)
Recommend ONE library for both sides (my default: the official `mcp` SDK low-level Server, because the tool list is dynamic). Write the confirmed facts with links into docs/API-NOTES.md under "MCP SDK", and propose the pinned line for integrations/requirements.txt. Commit as docs: on feat/gateway-mcp.
```

---

## G1 — Person A — gateway sessions in the backend (~3 h)

```text
Slice G1: backend side of the gateway, per the "Gateway API" section in contracts/README.md (already merged). Use the passport-gate, backend-conventions and api-contracts skills. Plan first, wait for my OK. Branch: feat/gateway-engine from main.

Build:
1. config.py: PASSPORT_GATEWAY_TOKEN (optional; when set must be ≥ 24 chars), GATEWAY_APPROVAL_WAIT_S (default 40, 5–55).
2. A gateway session is a normal Session with mode="gateway": its own SegmentStore, its own World (used only for redaction, canaries and the vault, NEVER to run a tool), its own Bus, decisions persisted like other sessions. No LLM, no agent loop. Prefer making the Session fields optional or a small subclass; don't fork decide(). Store agent_name and client (DB migration 002 + docs/DATABASE.md). Sessions are isolated: one session's segments, approvals and decisions never affect another (test it).
3. Routes (new file app/api/gateway_routes.py, registered in main.py):
   - token check dependency: missing env → 503 gateway_disabled; wrong/missing header → 401 gateway_unauthorized (compare_digest). Body size limit applies; rate limit per token: 300/min.
   - /intent: first call builds the capsule with build_capsule(request) and adds the USER segment; second call → 409 intent_locked (and an audit row "gateway_intent_rejected").
   - /decide: no intent → 409. Else decide(ctx, tool, args, step) exactly as the agent loop does. REQUIRE_APPROVAL with shield on → register in PENDING, emit approval_needed, await up to GATEWAY_APPROVAL_WAIT_S, set decision.approval to approved / rejected / timeout. shield_on=false → run=true with the decision unchanged (the UI shows the ghost stamp). Emit `decision` (twice, as today) and `gateway_call`. Audit row "gateway_decide" with tool, verdict, rule_id, redacted args, run.
     Fail closed: any exception in this route → {decision: R0 DENY, run: false}, never a 500 that a caller could misread.
   - /observe: only once per decision, only if that decision had run=true in this session. Ingest the output into the store with the trust from TOOLS[tool].output_trust (unknown tool → UNTRUSTED); secret outputs also go into world.vault so R4 and redaction cover them. Emit tool_result with a redacted preview.
   - GET /v1/gateway/sessions for the dashboard.
4. Tests (tests/test_gateway_api.py), each one fails without the code:
   - no token env → 503; wrong token → 401
   - s2 flow over HTTP: intent "Summarise my unread emails and reply to Asha with the summary"; decide list_unread_emails → ALLOW; observe the s2 inbox JSON; decide send_email to the attacker address from the hidden instruction → DENY R3 with evidence pointing at the email line; decide send_email to Asha → ALLOW
   - decide before intent → 409; second intent → 409
   - observe for a DENY'd decision → 409; observe twice → 409; caller can't choose the trust label
   - secret observed, then send_email with that secret in the body → DENY (R4 or R2)
   - REQUIRE_APPROVAL: approved via POST /approvals within the wait → run=true; no answer → run=false with approval "timeout" (set the wait to 1 s in the test)
   - two sessions: an approval or segment in session A never changes a verdict in session B
   - shield_on=false: run=true, verdict still DENY in the decision
   - monkeypatch decide to raise → run=false, rule R0
5. Regenerate contract examples (scripts/make_contract_examples.py) for the new endpoints.

Done when: tests above green, make check green, make eval unchanged (attacks 9/9 → 0/9, legit 7/7 → 7/7, 0 popups), PROGRESS.md updated, /checkpoint. Then run the red-teamer agent on the gateway routes and fix what it finds before merging.
```

---

## G2 — Person B — fake upstream + gateway + fooled agent (~3 h)

```text
Slice G2: the MCP side of the gateway. Use the library and versions confirmed in docs/API-NOTES.md "MCP SDK" (GB0). Follow contracts/README.md "Gateway API" exactly. Don't edit backend/app or frontend; if the API needs a change, stop and tell me (Person A owns it). Plan first, wait for my OK. Branch: feat/gateway-mcp.

New folder integrations/ with integrations/requirements.txt (pinned mcp + httpx), and:

1. integrations/nimbus_mcp/server.py — the "fake Gmail": an MCP server over stdio exposing the World tools with the same names, params and descriptions as backend/app/tools/registry.py TOOLS (import World/TOOLS/validate_args/run_tool from backend read-only via PYTHONPATH=backend). Inbox from env NIMBUS_INBOX (default base; s2_hidden_instruction for the demo). It refuses to start unless env NIMBUS_GATEWAY_KEY is set and ≥ 32 chars. So adding it to Claude Desktop directly, without the gateway, fails: "this server is only reachable through PASSPORT". All data synthetic; nothing leaves the process. Log to stderr only.

2. integrations/passport_gateway/server.py — the gateway, an MCP server over stdio for the agent:
   - On start: generate NIMBUS_GATEWAY_KEY = secrets.token_hex(32), launch nimbus_mcp as a child over stdio with that key in ITS env only (never printed, never sent to the agent), list its tools. POST /v1/gateway/sessions with agent_name from env PASSPORT_AGENT_NAME (default "Claude Desktop"), client = clientInfo name from initialize if available, shield_on from PASSPORT_SHIELD (on|off, default on).
   - Exposes: start_task(request) + every upstream tool with its schema. start_task's description says: "Call this FIRST with the user's exact request, before any other tool."
   - start_task → POST /intent. 409 → tool error "intent is locked for this session".
   - Any other tool → POST /decide (timeout = GATEWAY_APPROVAL_WAIT_S + 10 s).
     · run=false → MCP tool error "PASSPORT <VERDICT> <rule_id>: <message>" plus the evidence where-line. The upstream tool is NOT called.
     · run=true → call upstream, then POST /observe with the output, and ONLY THEN return the output to the agent.
   - Fail closed → tool error "PASSPORT unreachable or refused, failing closed", upstream never called (or its output never returned) when:
     · the backend is down, times out, returns non-2xx, or sends a body that isn't valid JSON of the expected shape;
     · the tool is not in the upstream list;
     · the upstream call errors;
     · observe fails.
   - Env: PASSPORT_URL, PASSPORT_GATEWAY_TOKEN, PASSPORT_SHIELD, PASSPORT_AGENT_NAME, NIMBUS_INBOX. Never log the tokens or tool outputs; one stderr line per call: tool, verdict, rule_id, run.
   - stdio by default; --http --port 8765 for the MCP Inspector if the SDK supports it cleanly (skip if not).

3. integrations/demo_agent/fooled_agent.py — a scripted "agent that fell for the email": an MCP client that launches the gateway over stdio and plays the s2 story step by step, printing each call and PASSPORT's answer in plain words: start_task("Summarise my unread emails and reply to Asha with the summary") → list_unread_emails → send_email to the attacker address found in the hidden instruction → send_email to Asha. Flag --shield off to show the attack going through in monitor mode. This is the reproducible demo; real Claude may refuse the injection on its own.

4. Until G1 is merged, test against a small stub backend (FastAPI app inside integrations/tests/, same contract, canned verdicts). After G1 is on main: git merge main, and switch the tests to the real backend app.

5. Makefile: gateway (runs the gateway over stdio), fooled-agent, gateway-test. README in integrations/ comes in G4.

Done when: fooled_agent.py runs end to end against the stub (then the real backend), stdout of the gateway carries only protocol traffic, nimbus_mcp refuses to start without the key, make check green, /checkpoint.
```

---

## G3 — Person A — "Gateway" tab in the dashboard (~3 h, after G1 merged)

```text
Slice G3: a "Gateway" tab in the frontend (4th tab after Agent, Scoreboard, Audit). Use frontend-conventions and project-ui; types first in src/lib/api/types.ts from contracts/README.md; all calls via src/lib/api/client.ts. Plan first, wait for my OK. Branch: feat/gateway-ui from main.

Layout (projector first, 1280×720):
- Left column "Connected agents": one row per gateway session from GET /v1/gateway/sessions (poll every 3 s): agent name, client, shield on/off, intent (one line, truncated), counts as small ALLOW / ASK / DENY numbers, status. Newest first. Empty state: "No agent connected. Start Claude Desktop with the PASSPORT gateway, or run make fooled-agent." with the two commands.
- Right: the selected session's live decisions, reusing DecisionCard, Stamp, EvidenceDrawer and the useRun reducer over GET /sessions/{id}/events (same SSE handling, dedupe by seq). Header: agent name + intent + "Calls go through PASSPORT; the agent holds no tool credentials."
- Approval center: when an approval_needed arrives for ANY gateway session, show the existing ApprovalDialog with the tool, the exact args, the reason and a countdown of the remaining wait (from GATEWAY_APPROVAL_WAIT_S in the event or decision ts). Approve/Reject → POST /approvals/{id}. After the countdown: "Timed out. The call was refused (fail closed). Ask the agent to retry."
- The Audit tab already shows gateway rows; add a filter chip "Gateway" if it is cheap.
Keep the existing three tabs working unchanged. Run the screenshot loop (desktop + --projector) with a session created by make fooled-agent, then the ui-critic agent. make check green, /checkpoint.
```

---

## G4 — Person B — real end-to-end + Claude Desktop (~2.5 h)

```text
Slice G4: prove the gateway end to end and make it usable from a real MCP client. Plan first, wait for my OK. Branch: feat/gateway-mcp (after merging main with G1).

1. integrations/tests/test_e2e.py, with the real backend app (uvicorn on a free port started by the test fixture, or the SDK's in-memory transport plus httpx ASGI transport if the gateway can be pointed at it), each one fails without the code:
   - s2 story: start_task, list ALLOW, attacker send_email → tool error with DENY R3 and the email line, Asha send_email ALLOW; the World's sent mail contains Asha only
   - tool before start_task → refused; second start_task → refused
   - backend stopped → every tool refused "failing closed", upstream never called
   - backend returns garbage / 500 → refused
   - unknown tool name → refused
   - read_secret (not in the profile) → DENY R1
   - nimbus_mcp without NIMBUS_GATEWAY_KEY → refuses to start
   - the key never appears in anything sent to the agent (tool list, results, errors)
   - PASSPORT_SHIELD=off → attacker send goes through, decision still says DENY (monitor mode)
   Keep them under 30 s. Add `make gateway-test`; add it to scripts/check.sh only if it runs in under 15 s with no extra install, otherwise add a CI step that installs integrations/requirements.txt.
2. integrations/README.md:
   - what it is;
   - setup on Windows and macOS;
   - the claude_desktop_config.json block (command = the venv python, args = the gateway path, env = PASSPORT_URL, PASSPORT_GATEWAY_TOKEN, NIMBUS_INBOX=s2_hidden_instruction): no upstream credential in it;
   - the MCP Inspector command;
   - the demo script;
   - honest limits (only tools routed through PASSPORT; the intent is what the client reports; don't also configure the raw server).
3. Try it in Claude Desktop with the prompt "Summarise my unread emails and reply to Asha with the summary". Record what really happened in docs/AI-LOG.md (did Claude call start_task? did it follow the hidden instruction? what did PASSPORT answer?). If Claude refuses the injection, that is fine: the demo uses fooled_agent.py for the attack and Claude Desktop for the legit flow.
4. docs/RESULTS.md: a "Gateway" table filled ONLY from the e2e test run output.
make check green, /checkpoint.
```

---

## G5 — both — red-team, review, pitch (08:00–10:00)

Person A:
```text
Run the red-teamer agent against the gateway (integrations/ and app/api/gateway_routes.py). Targets:
· calls that skip /decide;
· observe abuse (fake trusted content, replay, other session's decision);
· approval reuse;
· token leaks in logs and errors;
· session crossover;
· oversized or malformed MCP arguments;
· upstream output that pretends to be a PASSPORT message.
Every bypass becomes a failing test first, then a fix. Then the reviewer agent on the diff since main@G0. Fix blocking findings only.
```
Person B:
```text
Update docs/PITCH.md and the slides text for the gateway story, using only numbers from make eval and the gateway e2e run (FACTS.md for anything else):
- Opening line: "You don't switch agents. Keep Claude Desktop; PASSPORT checks every tool call it makes."
- 3-minute demo order:
  1. fooled_agent --shield off: the attack goes through;
  2. fooled_agent with the shield on: DENY with the email line;
  3. Claude Desktop legit task + one approval from the dashboard;
  4. stop the backend: everything is refused (fail closed);
  5. Audit verify.
- Judge Q&A:
  · Does this work with Gmail's own Gemini? (No: Google runs those tools; we protect agents whose tools route through PASSPORT.)
  · What if the user adds the raw server? (Not reachable without the gateway key; config bypass is a stated limit.)
  · Real Gmail? (Roadmap: OAuth connector + credential vault; never in the demo.)
- Roadmap slide: remote HTTPS gateway with MCP auth, real connectors + credential vault, policy editor, more clients, SDK.
Then run prompts/99-demo-prep.md.
```

## If you run late
- 04:30 G1 not merged → B keeps the stub and A cuts the observe-once tests last.
- 08:00 Claude Desktop not working → demo with fooled_agent.py + MCP Inspector, and say so honestly.
- 08:00 G3 not done → show gateway decisions in the existing Agent tab by opening the session id (works because gateway sessions are normal sessions).
- Never merge anything red after 11:00.
