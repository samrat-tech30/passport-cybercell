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

## External services
- LLM provider: check with `cd backend && .venv/Scripts/python scripts/llm_probe.py [--base-url --model --key-var]`, then `scripts/live_trials.py s1 --runs 5`.
  - Ollama 0.40.13 local, `http://localhost:11434/v1`, `llama3.2:latest` (3B), key: any value: probe returns a correct single tool call (11.6 s cold). **Not good enough for the agent:** in S1 x5 and S2 x3 (shield OFF) it never called `list_unread_emails`; it sent Priya a fake summary ("See list_unread_emails() for details") in one step, so it never saw Email #3. Not a refusal: it can't chain tool calls (tested, 2026-10-30)
  - Hosted provider (Groq / OpenRouter / other): **not tested yet**, no key in backend/.env
