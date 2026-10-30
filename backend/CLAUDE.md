# Backend rules (in addition to the root CLAUDE.md)

- **Stack:** Python 3.11+ (tested on 3.13; Docker uses 3.12), FastAPI 0.162, Pydantic 2.14, PyYAML, SQLite (stdlib `sqlite3`), openai SDK 3.41 (OpenAI-compatible client for live mode), pytest, ruff. Exact pins: `requirements*.txt`. Add nothing else without asking. v2 may add `PyJWT[crypto]` (payment visa).
- Follow the `backend-conventions` skill (layers) and, for anything in `app/gate/`, `app/tools/`, `app/scenarios/`, the `passport-gate` skill.

## Layout
| Path | What | Never |
|---|---|---|
| `app/main.py` | app wiring: middleware, error format, routes | business logic |
| `app/config.py` | every env var, validated once | read `os.environ` anywhere else |
| `app/contracts.py` | shared shapes (mirrors `../contracts/README.md`) | change without the contract |
| `app/api/` | routes (thin) + request schemas (strict, `extra="forbid"`) | SQL, gate logic |
| `app/gate/` | **the product**: policy.yaml, segments, capsule, tracer, decide, handle | network, LLM calls, randomness in decisions |
| `app/tools/` | fake world + tool catalogue | real network, real file writes |
| `app/agent/` | agent loop, LLM back-ends, prompt | call tools directly |
| `app/db/` | SQLite: connection, migrations, audit chain, queries | business rules |
| `app/scenarios/*.yaml` | scenarios with scripted plans + expected verdicts | real data |
| `app/eval_runner.py` | shield OFF vs ON evaluation | invented numbers |
| `tests/` | pytest; expected values worked out by hand | compute expectations with the code under test |

## Commands (run inside `backend/`, venv active: `source .venv/bin/activate`, Windows: `.venv\Scripts\activate`)
- dev: `uvicorn app.main:app --reload --port 8000 --env-file .env`
- test: `pytest` · lint: `ruff check . && ruff format --check .` · eval: `python -m app.eval_runner`
- migrate: automatic at start-up (`app/db/database.py` applies `app/db/migrations/*.sql` in order)
