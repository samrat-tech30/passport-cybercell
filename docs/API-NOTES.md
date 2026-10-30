# API notes (library behaviour already checked)

`- <api>: <what is true> (<tested|read>, <pkg@version>, <date>)`

## Backend
- fastapi 0.162 + starlette 1.10: `TestClient` runs `asyncio.create_task` background runs; SSE via `StreamingResponse(media_type="text/event-stream")` works with `client.stream()` (tested, 2026-10-30)
- Pure ASGI middleware is used for headers/body limit so SSE streaming isn't buffered (tested, 2026-10-30)
- openai 3.41: `AsyncOpenAI(base_url, api_key, timeout, max_retries)` and `client.chat.completions.create(model, messages, tools, tool_choice, temperature)` exist (read signature, 2026-10-30). **Live call not tested yet.**
- uvicorn 0.54 `--env-file .env` loads `KEY=value  # comment` lines correctly (python-dotenv bundled with uvicorn[standard]) (tested, 2026-10-30)
- Python 3.11+ needed (`enum.StrEnum`); tested on 3.13 (2026-10-30)

## Frontend
- typescript 7.0.2 ships a `tsc` binary; `tsc --noEmit` works with `moduleResolution: bundler`, `verbatimModuleSyntax`, `types: ["vite/client"]` (tested, 2026-10-30)
- vite 8.3.5 needs Node ^20.19 or >=22.12; @vitejs/plugin-react 6.1.2 peers are optional (tested, 2026-10-30)
- `EventSource` can't send custom headers → the events endpoint is a GET with no access code; it reconnects with `Last-Event-ID`, which the backend honours (tested, 2026-10-30)

## External services
- LLM provider: <fill after M1's test: base URL, model name, tool-calling OK?, rate limit, free tier> (source, date)
