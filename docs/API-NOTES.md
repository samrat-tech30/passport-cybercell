# API notes (library behaviour already checked)

`- <api>: <what is true> (<tested|read>, <pkg@version>, <date>)`

## Backend
- fastapi 0.162 + starlette 1.10: `TestClient` runs `asyncio.create_task` background runs; SSE via `StreamingResponse(media_type="text/event-stream")` works with `client.stream()` (tested, 2026-10-30)
- Pure ASGI middleware is used for headers/body limit so SSE streaming isn't buffered (tested, 2026-10-30)
- openai 3.41: `AsyncOpenAI(base_url, api_key, timeout, max_retries)` and `client.chat.completions.create(model, messages, tools, tool_choice, temperature)` work against a real server (tested against Ollama, 2026-10-30)
- openai 3.41 is built on **`httpx2`** (2.16), not `httpx`: build test exceptions with `httpx2.Request/Response`. `RateLimitError(msg, response=, body=)`, `APITimeoutError(request=)`; `APITimeoutError` subclasses `APIConnectionError`, `RateLimitError` subclasses `APIStatusError` (tested, 2026-10-30)
- openai 3.41: `client.chat.completions.with_raw_response.create(...)` returns an object with `.headers` and `.parse()` (read + tested in `scripts/llm_probe.py`, 2026-10-30)
- uvicorn 0.54 `--env-file` calls `load_dotenv(path)` with `override=False`: variables already set in the shell win over `.env` (read source, 2026-10-30)
- uvicorn 0.54 `--env-file .env` loads `KEY=value  # comment` lines correctly (python-dotenv bundled with uvicorn[standard]) (tested, 2026-10-30)
- Python 3.11+ needed (`enum.StrEnum`); tested on 3.13 (2026-10-30)

## Frontend
- typescript 7.0.2 ships a `tsc` binary; `tsc --noEmit` works with `moduleResolution: bundler`, `verbatimModuleSyntax`, `types: ["vite/client"]` (tested, 2026-10-30)
- vite 8.3.5 needs Node ^20.19 or >=22.12; @vitejs/plugin-react 6.1.2 peers are optional (tested, 2026-10-30)
- `EventSource` can't send custom headers → the events endpoint is a GET with no access code; it reconnects with `Last-Event-ID`, which the backend honours (tested, 2026-10-30)

## MCP SDK (GB0, for integrations/)
- Versions on PyPI 2026-10-31: `mcp` 2.3.0 (official SDK), `fastmcp` 4.1.4. Both `Requires-Python >=3.10`, classifiers list 3.11–3.14 (read, 2026-10-31). Tested on Python 3.14.3 locally; 3.11–3.13 not run.
- **Recommendation: official `mcp` 2.3.0 low-level `Server` on both sides.** The tool list is dynamic (copied from upstream + `start_task`), which the low-level server does with one handler. `fastmcp` 4.x no longer depends on `mcp` (only `mcp-types`), so mixing them buys nothing (read `pip show`, 2026-10-31).
- mcp 2.x API differs from 1.x: handlers are **constructor arguments**, not decorators: `Server("name", on_list_tools=fn, on_call_tool=fn)`; `fn(ctx, params)` is async. `on_list_tools` returns `mcp_types.ListToolsResult(tools=[mcp_types.Tool(name, description, input_schema={...})])`. `on_call_tool` gets `params.name` / `params.arguments` and returns `mcp_types.CallToolResult(content=[mcp_types.TextContent(type="text", text=...)], is_error=...)`. Types live in the separate package `mcp_types` (snake_case fields: `input_schema`, `is_error`) (tested, mcp@2.3.0, 2026-10-31)
- Refusing a call: return `CallToolResult(..., is_error=True)`; the client gets `is_error=True` and the text. **Raising** in the handler gives the client `MCPError: Internal server error` (protocol error, no message) and a traceback on the server's stderr, so the gateway must catch and return `is_error` (tested, mcp@2.3.0, 2026-10-31)
- Run over stdio: `async with mcp.server.stdio.stdio_server() as (r, w): await server.run(r, w, server.create_initialization_options())`. While serving, fd 1 is pointed at stderr, so stray `print()`s don't corrupt the protocol (read source + tested: a `print()` in a handler did not break the session, 2026-10-31)
- Client info inside a handler: `ctx.session.client_params.client_info.name` (`client_params` may be None on the 2026-07-28 protocol era; guard it). The SDK's own `Client` reports `"mcp"` (tested, mcp@2.3.0, 2026-10-31)
- Client: `from mcp import Client`; `Client(StdioServerParameters(command, args, env, cwd))` launches a child; `async with Client(...) as c:` initializes; `await c.list_tools()` → `.tools`; `await c.call_tool(name, args)` → `CallToolResult` (`.is_error`, `.content[i].text`). `env` is merged over `get_default_environment()`, which on Windows/POSIX passes only a safe allowlist (PATH, HOME, …), so the parent's other env vars (tokens) are **not** inherited by the child (read source + tested, mcp@2.3.0, 2026-10-31)
- A child that exits at startup (e.g. nimbus without its key) makes `async with Client(params)` raise an `ExceptionGroup` (tested, 2026-10-31)
- In-memory tests without subprocesses: `Client(server)` where `server` is a low-level `Server` connects in-process. A gateway `Server` whose upstream is a real stdio child works this way too (tested, mcp@2.3.0, 2026-10-31)
- Streamable HTTP: `app = server.streamable_http_app(host="127.0.0.1")` returns a Starlette app serving `/mcp` (DNS-rebinding protection on by default for localhost); run with `uvicorn`; connect with `Client("http://127.0.0.1:8765/mcp")` (tested end to end, mcp@2.3.0 + uvicorn, 2026-10-31)
- MCP Inspector (needs Node ≥ 22.19; we have 24.13.1): stdio `npx @modelcontextprotocol/inspector <command> <args>`; HTTP `npx @modelcontextprotocol/inspector --server-url http://127.0.0.1:8765/mcp --transport http`; `--cli ... --method tools/list` for a scripted check. Stdio `env:` values are stored in the OS keychain (read https://modelcontextprotocol.io/docs/tools/inspector, 2026-10-31). Not run yet.
- Claude Desktop config file: Windows `%APPDATA%\Claude\claude_desktop_config.json`, macOS `~/Library/Application Support/Claude/claude_desktop_config.json`. Shape: `{"mcpServers": {"<name>": {"command": "...", "args": [...], "env": {...}}}}`; absolute paths; fully quit and restart after editing. Logs: Windows `%APPDATA%\Claude\logs`, macOS `~/Library/Logs/Claude`; `mcp-server-<NAME>.log` holds the server's stderr (read https://modelcontextprotocol.io/docs/develop/connect-local-servers, 2026-10-31)
- Claude Desktop tool-call timeout: **not verified** (no official source found). Assumed ~60 s per GATEWAY-PROMPTS.md, hence GATEWAY_APPROVAL_WAIT_S=40. How to check: an approval that waits 50 s, see whether Claude Desktop gives up.
- Proposed `integrations/requirements.txt`: `mcp==2.3.0`, `httpx==0.28.1` (same httpx pin as the backend; mcp itself pulls `httpx2`, `uvicorn`, `starlette`).
## MCP
- `@modelcontextprotocol/sdk` 1.32.2 (TypeScript, latest on npm 2026-10-31): `DEFAULT_REQUEST_TIMEOUT_MSEC = 60000` in `shared/protocol.js`; `request()` uses `options.timeout ?? 60000` and fails with "Request timed out". Progress notifications reset the timer only if the client passes `resetTimeoutOnProgress: true`. So `GATEWAY_APPROVAL_WAIT_S` must stay well under 60. Which timeout Claude Desktop / Cursor actually pass: not verified yet (read unpkg source, 2026-10-31)

## Gmail (integrations/gmail_mcp, read 2026-10-31)
- OAuth for desktop apps (developers.google.com/identity/protocols/oauth2/native-app): auth `https://accounts.google.com/o/oauth2/v2/auth`, token `https://oauth2.googleapis.com/token`; loopback redirect `http://127.0.0.1:<port>`; PKCE `code_challenge_method=S256`; "refresh tokens are always returned for installed applications"; client_secret listed as optional (we send it). Loopback still supported for Desktop app clients (loopback-migration page). Whether any port works without registering it: not stated; we use a random port (read)
- `users.messages.list` `GET https://gmail.googleapis.com/gmail/v1/users/me/messages?q=is:unread in:inbox&maxResults=10` → `messages[].id` only; scope gmail.readonly is enough (read)
- `users.drafts.create` `POST …/users/me/drafts` body `{"message": {"raw": <base64url RFC 2822>}}`; scopes mail.google.com, gmail.modify or **gmail.compose** (read). Note: gmail.compose also allows sending; our code never calls a send endpoint, and a test asserts it
- Not verified yet: a real sign-in and real API calls (needs your Google Cloud client)

## External services
- LLM provider: check with `cd backend && .venv/Scripts/python scripts/llm_probe.py [--base-url --model --key-var]`, then `scripts/live_trials.py s1 --runs 5`.
  - Ollama 0.40.13 local, `http://localhost:11434/v1`, `llama3.2:latest` (3B), key: any value: probe returns a correct single tool call (11.6 s cold). **Not good enough for the agent:** in S1 x5 and S2 x3 (shield OFF) it never called `list_unread_emails`; it sent Priya a fake summary ("See list_unread_emails() for details") in one step, so it never saw Email #3. Not a refusal: it can't chain tool calls (tested, 2026-10-30)
  - Groq `https://api.groq.com/openai/v1` (base URL from console.groq.com/docs/openai), `openai/gpt-oss-120b`, free plan: probe OK in 0.9 s; headers say 1000 requests/day, 8000 tokens/min. Back-to-back S2 runs hit HTTP 429 (tokens/min) on the last turn; with `--pause 25` none did. S1 x5: 5/5 correct (read inbox, real summary to Priya). S2 x9 shield OFF (new persona): read_secret 9/9, leak to evil.test 2/9; the other 7 claimed in the final text to have sent the key without calling send_email. Shield ON: read_secret DENY, not run; Priya ALLOW (tested, 2026-10-30)
