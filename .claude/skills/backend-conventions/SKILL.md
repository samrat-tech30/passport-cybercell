---
name: backend-conventions
description: Conventions for backend/ - layers (api, gate, tools, agent, db, config), strict request validation, the error format, config and env validation, the backend's own security (headers, CORS, rate limits, access code, body limit), SQLite migrations, logging without secrets, and tests. Use when creating or changing anything in backend/ (plus passport-gate for gate/tools/scenarios).
---

# Backend conventions

**Stack:** Python 3.11+, FastAPI 0.162, Pydantic 2.14, PyYAML, stdlib sqlite3, openai SDK 3.41 (live mode only), pytest, ruff. Nothing else without asking.

## Layers (each calls only the ones below it)
| Layer | Path | Does | Never |
|---|---|---|---|
| api | `app/api/routes.py`, `schemas.py` | validate input (strict models), call a module, shape the reply per contracts | SQL, gate logic |
| sessions / agent | `app/sessions.py`, `app/agent/` | run the agent loop, approvals, events | call tools directly |
| gate | `app/gate/` | decide, label, execute via handle.py | network, LLM, DB writes except through `repo`/`audit` |
| tools | `app/tools/` | fake world effects in memory | real network or file writes |
| db | `app/db/` | connection, migrations, audit chain, queries | business rules |
| config | `app/config.py` | read + validate every env var once | be bypassed with `os.environ` elsewhere |

## Rules
- **Request models** inherit `Strict` (`extra="forbid"`), every string has `max_length`, ids have a `pattern`.
- **Errors** always `{"error": {"code": "snake_case", "message": "plain words"}}` via `HTTPException(detail={...})`. 400 bad input, 401 access code, 404 not found, 413 too big, 422 validation, 429 rate limited, 500 our fault (no stack trace in the body).
- **State-changing routes** (POST) get `Depends(require_access)`; expensive ones also `Depends(rate_limit("<bucket>"))`.
- **CORS** only the origins in `ALLOWED_ORIGINS`; never `*`; no credentials.
- **Security headers** come from `SecurityHeadersMiddleware` (pure ASGI, safe for SSE). Don't switch to `BaseHTTPMiddleware`.
- **SQL** only in `app/db/`, always `?` parameters. Schema changes = a new file `app/db/migrations/00N_name.sql`; never edit an applied migration. Update docs/DATABASE.md.
- **Audit**: append through `app/db/audit.py` with already-redacted data. Never update or delete audit rows in code.
- **Logs**: no request bodies, no tool arguments, no secrets. Log a decision id and rule id instead.
- **Live LLM**: one client in `app/agent/llm.py` with a timeout; replay mode must keep working with no network.
- **Tests**: pytest, fresh temp DB per test (`tests/conftest.py`), no network. Route tests use FastAPI `TestClient`. Expected values by hand.

## Commands (inside backend/, venv active)
dev `uvicorn app.main:app --reload --port 8000 --env-file .env` · test `pytest` · lint `ruff check . && ruff format --check .` · eval `python -m app.eval_runner`
