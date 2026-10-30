# PASSPORT

**Every argument needs a passport.** A security gate between an AI agent and its tools: before any tool runs, every important argument (recipient, file path, account, amount) is traced to where it was born. Values born in untrusted content (emails, files, web pages) can't steer actions, and secrets can't leave, so a hidden instruction in an email can't hijack the agent while the user's real task still completes.

Parallax 2026 · AgentShield track · BMSCE. All data is synthetic.

## Results (measured with `make eval`, replay mode, our own scenario suite)
| Metric | Shield OFF | Shield ON |
|---|---|---|
| Attacks that got through | 7 / 7 | 0 / 7 |
| Legitimate tasks completed | 6 / 6 | 6 / 6 |
| Approval popups on clean legit tasks | - | 0 |

Details and limits: `docs/RESULTS.md`, `docs/THREAT-MODEL.md`.

## Run it (3 commands)
Needs Python 3.11+, Node 22.12+ (or 20.19+), make.
```bash
make setup      # backend venv + frontend packages + .env files from the examples
make backend    # terminal 1: API on http://localhost:8000
make frontend   # terminal 2: UI on http://localhost:5173
```
Then pick **S2**, turn the shield **off**, press **Run scenario**; turn it **on** and run again.

`make test` (backend tests) · `make eval` (OFF vs ON table) · `make check` (everything, must pass before merging).

### Without make (Windows PowerShell)
```powershell
cd backend; python -m venv .venv; .venv\Scripts\pip install -r requirements-dev.txt; copy .env.example .env
.venv\Scripts\uvicorn app.main:app --reload --port 8000 --env-file .env      # terminal 1
cd frontend; npm install; copy .env.example .env.local; npm run dev           # terminal 2
cd backend; .venv\Scripts\pytest; .venv\Scripts\python -m app.eval_runner     # tests, eval
```

## Repo map
| Path | What |
|---|---|
| `backend/` | FastAPI + SQLite. `app/gate/` is the product (policy.yaml, tracer, rules, handle). Deploys alone (Dockerfile). |
| `frontend/` | React + Vite + TypeScript UI. Deploys alone (static). |
| `contracts/` | API contract, real request/response examples, OpenAPI. |
| `docs/` | spec, architecture, threat model, security, database, plan, pitch, results, decisions. |
| `prompts/` | ready-to-paste Claude Code prompts for each teammate and each v2 upgrade. |
| `.claude/` | Claude Code kit: hooks, slash commands, agents, skills. |
| `design/mockups/` | screenshots of every screen (the UI reference). |

## How it works (short)
1. The user's request is frozen into an **intent capsule** before anything is read.
2. Everything the agent reads is labelled: user, trusted, untrusted, secret.
3. Each tool call goes through the gate: strict argument check → role profile → canary secrets (any encoding) → **trace every sink argument** → intent → high impact.
4. Verdict: ALLOW, NEEDS YOU (approval, timeout = no) or DENY, with the exact source line as evidence. Any error = DENY.
5. Every decision is stored in a **hash-chained audit log**.
Any agent framework can ask for a verdict with `POST /v1/decide` (`contracts/README.md`).

## Deploy
Two services from this one repo: backend root directory `backend/` (Docker), frontend root directory `frontend/` (static). Steps and env vars: `docs/DEPLOY.md`.

## Credits
Builds on published ideas: CaMeL (Google DeepMind), FIDES (Microsoft), PACT/ARGUS (argument-level provenance), Invariant Labs' MCP tool-poisoning research, OWASP Top 10 for LLM Applications. What's ours: `docs/PITCH.md`. AI use: `docs/AI-LOG.md`.
