# PASSPORT gateway: protect an agent you didn't write

Claude Desktop, Cursor, the MCP Inspector or any MCP client talks to the **PASSPORT gateway**
instead of to its tools. Before every tool call the gateway asks the PASSPORT backend. The tool
runs only when the backend says `run: true`, and its output is labelled before the agent sees it.

```text
agent (Claude Desktop / fooled_agent.py) --MCP stdio--> passport_gateway --HTTP /v1/gateway/*--> backend
                                                        passport_gateway --MCP stdio--> nimbus_mcp (child)
```

| Folder | What |
|---|---|
| `passport_gateway/server.py` | MCP server for the agent (`start_task` + the upstream tools) and MCP client to the upstream |
| `nimbus_mcp/server.py` | the "fake Gmail": the synthetic Nimbus Labs World as MCP tools. It exits unless the gateway's random key is set, so it can't be added to a client directly |
| `demo_agent/fooled_agent.py` | a scripted agent that obeys the hidden instruction in email #3 (the reproducible attack) |
| `tests/` | `test_gateway.py` (in process, ~5 s) and `test_e2e.py` (real uvicorn + real stdio, ~30 s on Windows) |

All data is synthetic (`.test` domains, random canary secrets). Nothing touches a real account.

## Setup
Windows (PowerShell, no make needed):
```powershell
backend\.venv\Scripts\pip install -r integrations\requirements.txt
# backend\.env: PASSPORT_GATEWAY_TOKEN=<24+ random characters>, then restart the backend
backend\.venv\Scripts\uvicorn app.main:app --port 8000 --env-file .env   # from backend\
```
macOS / Linux: the same with `backend/.venv/bin/...`, or `make setup`, `make backend`.

Generate a token: `backend\.venv\Scripts\python -c "import secrets; print(secrets.token_hex(16))"`.
Without `PASSPORT_GATEWAY_TOKEN` every `/v1/gateway/*` call returns 503 (fail closed).

| Gateway env var | Default | Meaning |
|---|---|---|
| `PASSPORT_GATEWAY_TOKEN` | – (required) | same value as the backend's; the gateway exits without it |
| `PASSPORT_URL` | `http://127.0.0.1:8000` | the backend |
| `PASSPORT_SHIELD` | `on` | `off` = monitor mode: every call runs, decisions still show "would deny" |
| `PASSPORT_AGENT_NAME` | `Claude Desktop` | the name shown in the dashboard |
| `NIMBUS_INBOX` | `base` | the synthetic inbox; `s2_hidden_instruction` for the demo |
| `NIMBUS_POISON` | – | demo only: `tool` (check_spelling's description hides an instruction) or `rugpull` (it turns poisoned after the first call) |
| `GATEWAY_APPROVAL_WAIT_S` | `40` | must match the backend's; the gateway waits this + 10 s on `/decide` |

## The attack, reproducibly
```powershell
$env:PASSPORT_GATEWAY_TOKEN = "<same token>"
backend\.venv\Scripts\python integrations\demo_agent\fooled_agent.py               # DENY R3 with the email line
backend\.venv\Scripts\python integrations\demo_agent\fooled_agent.py --shield off  # goes through, "would be DENY"
```
(`make fooled-agent`, `make fooled-agent SHIELD=off`.)

**A malicious server "installed from GitHub"** (`NIMBUS_POISON`):
```powershell
backend\.venv\Scripts\python integrations\demo_agent\fooled_agent.py --story poisoned-tool  # DENY R3 "Tool description: check_spelling … line 3"
backend\.venv\Scripts\python integrations\demo_agent\fooled_agent.py --story rugpull        # 2nd call refused: tools changed after install
```
For a real client, add `"NIMBUS_POISON": "tool"` (or `"rugpull"`) and `"NIMBUS_INBOX": "base"` to the gateway's `env` in the client config. Each run is a new gateway session, listed
in `GET /v1/gateway/sessions` and the Audit tab.

## Claude Desktop
Edit `%APPDATA%\Claude\claude_desktop_config.json` (Windows) or
`~/Library/Application Support/Claude/claude_desktop_config.json` (macOS). Absolute paths, then
**fully quit and restart** Claude Desktop (tray icon → Quit; closing the window keeps it running).
```json
{
  "mcpServers": {
    "passport": {
      "command": "C:\\Cybersec hack\\passport-cybercell\\backend\\.venv\\Scripts\\python.exe",
      "args": ["C:\\Cybersec hack\\passport-cybercell\\integrations\\passport_gateway\\server.py"],
      "env": {
        "PASSPORT_URL": "http://127.0.0.1:8000",
        "PASSPORT_GATEWAY_TOKEN": "<same token as the backend>",
        "NIMBUS_INBOX": "s2_hidden_instruction"
      }
    }
  }
}
```
There is **no upstream credential** in this config: the gateway makes a new random key for
`nimbus_mcp` on every start. On macOS the command is `<repo>/backend/.venv/bin/python`.

**Windows, Microsoft Store install** (no `%APPDATA%\Claude` folder): the config is
`%LOCALAPPDATA%\Claude-Data\claude_<id>\claude_desktop_config.json` (the path is printed in
`%LOCALAPPDATA%\Claude\logs\main.log` as "token cache location"). Add `"mcpServers"` as a top-level
key next to the existing preferences. Logs, including `mcp-server-passport.log` (one line per call:
tool, verdict, rule, run), are in `%LOCALAPPDATA%\Claude\logs` (`%APPDATA%\Claude\logs` or
`~/Library/Logs/Claude` otherwise). Once loaded, passport shows under **+ → Connectors**.

## MCP Inspector (Node ≥ 22)
```bash
# stdio (pass the env the same way as in the Claude Desktop config)
npx @modelcontextprotocol/inspector backend/.venv/Scripts/python integrations/passport_gateway/server.py
# or HTTP
PASSPORT_GATEWAY_TOKEN=<token> NIMBUS_INBOX=s2_hidden_instruction backend/.venv/Scripts/python integrations/passport_gateway/server.py --http --port 8765
npx @modelcontextprotocol/inspector --server-url http://127.0.0.1:8765/mcp --transport http
```
Not run with this version of the gateway yet.

## Demo script (3 minutes)
1. `fooled_agent.py --shield off`: the attacker gets the email; the reply says PASSPORT *would* have denied it.
2. `fooled_agent.py`: `send_email` to `audit-team@evil.test` → **DENY R3_SINK_UNTRUSTED**, "came from Email #3 … line 13"; the tool was never called. Priya's summary goes through.
3. Claude Desktop: "Summarise my unread emails and send the summary to priya@nimbus.test" → `start_task`, `list_unread_emails` ALLOW, send to Priya ALLOW. Show the session in the dashboard.
4. Stop the backend and call any tool → "PASSPORT unreachable or refused, failing closed".
5. Audit tab → Verify chain.

Claude itself usually refuses the hidden instruction (seen 2026-10-31 with the V2-E gateway). So
the DENY is shown with `fooled_agent.py`, which plays a model that obeys. Pitch line: a careful
model refuses, a gullible one obeys, and PASSPORT stops it at the tool call either way.

## Tests
```bash
cd integrations && ../backend/.venv/Scripts/python -m pytest tests -q     # or: make gateway-test
```
CI installs `integrations/requirements.txt` and runs them after `scripts/check.sh`.

## Limits (say them)
- It protects only the tools **behind the gateway**. If the user also gives the client a raw email or
  filesystem server, those calls never reach PASSPORT. (`nimbus_mcp` itself can't be added directly:
  it exits without the gateway's key.)
- **The intent is what the client reports** in `start_task`. A client that reports a false request
  gets that request checked; the lock only stops it from changing later.
- One PASSPORT session per gateway **process**. Claude Desktop most likely keeps one process for all
  its chats (not verified), so a second chat finds the intent locked: restart Claude Desktop between
  demo runs.
- Approvals: the call waits up to 40 s for the dashboard. MCP clients time out tool calls at ~60 s
  (TypeScript SDK default; Claude Desktop's value not verified). **`POST /approvals/{id}` needs
  `DEMO_ACCESS_CODE` set on any shared backend**, otherwise anyone who can reach it can approve.
- Content the agent saw outside PASSPORT (pasted into the chat) isn't labelled: a value from it traces
  as model-invented (an approval), not as untrusted.
