# PASSPORT: instructions for Claude Code

@AGENTS.md

You are helping a team of 4 (BMSCE) build **PASSPORT** for **Parallax 2026** (IEEE Computer Society BMSCE, 24-hour defensive cybersecurity hackathon, 30–31 Oct 2026). Track: **AgentShield, "secure the agent, not just the prompt"**. **Submissions close 16:00 on 31 Oct, strict. Code freeze 12:00.** Judges see a live demo from `main`, so main must always work.

**The product (3 sentences):** PASSPORT is a security gate between an AI agent and its tools. Before any tool runs, it traces every important argument (recipient, path, account, amount) back to where it was born: the user's words, trusted config, a secret, or untrusted content such as an email. Values born in untrusted content can't steer actions and secrets can't leave, so a hidden instruction in an email can't hijack the agent, while the user's real task still completes.

**Judging criteria (8):** threat relevance · verified effectiveness (attack works before, fails after) · technical implementation · innovation · UI/UX · safety & responsible engineering · feasibility & impact · presentation & live demo.

**Stack:** backend Python 3.11+ / FastAPI / Pydantic v2 / SQLite in `backend/`; frontend React 19 + Vite 8 + TypeScript 7 + plain CSS tokens in `frontend/`. No LangChain in the core (decision in `docs/DECISIONS.md`). Allowed packages are listed in `backend/CLAUDE.md` and `frontend/CLAUDE.md`: add nothing else without asking.

## Start of every session
- The SessionStart hook has already put `docs/PROGRESS.md`, `docs/LESSONS.md` and the git state in your context. Read them first.
- Read only what the task needs (table below). Don't read the whole repo.

## Where the truth lives (check here; never guess)
| Question | Source |
|---|---|
| What we build, scenarios, demo path | `docs/SPEC.md` |
| How the parts fit, data flow, the rules R0–R8 | `docs/ARCHITECTURE.md`, `backend/app/gate/policy.yaml` |
| Threat model (attacker, assets, what we stop / don't) | `docs/THREAT-MODEL.md` |
| Security of the app itself | `docs/SECURITY.md` |
| Database tables and migrations | `docs/DATABASE.md`, `backend/app/db/migrations/` |
| API shapes, errors | `contracts/README.md`, `contracts/examples/` |
| What "done" means per slice | `docs/ACCEPTANCE.md` |
| Plan, roles, timeline | `docs/PLAN.md` |
| Ready prompts for each task | `prompts/` |
| Look and screens | `docs/DESIGN.md`, `frontend/src/styles/tokens.css`, `design/mockups/*.png` |
| Any fact (number, incident, paper) | `docs/FACTS.md` |
| Library behaviour already checked | `docs/API-NOTES.md` |
| Why things are the way they are | `docs/DECISIONS.md` |

## Rules that must never be broken
1. **Tools run only through `backend/app/gate/handle.py`.** Nothing else calls a tool function or `run_tool()`. The guard hook checks this.
2. **Fail closed.** Any error, unknown tool, invalid argument or unanswered approval = DENY. Never add a code path that turns an exception into ALLOW.
3. **No LLM in the decision path.** The gate decides with deterministic code over data origins. An LLM may help elsewhere, never in `decide()`.
4. **Untrusted content can't steer a sink argument** (recipient, path, account, amount, secret key). Don't weaken R3 to make a demo pass; change the scenario or the policy with a test and a line in DECISIONS.md.
5. **Secrets never leave, never get logged.** Anything shown, stored, streamed or logged goes through `world.redact()`. Canary values are random per session; never hard-code one.
6. **All data is synthetic.** `.test` domains, fake names, fake accounts. Tools never touch the real network or real files (delete/pay/send are in-memory). **One exception, approved by Samrat (2026-10-31):** the opt-in real Gmail connector `integrations/gmail_mcp` (`PASSPORT_UPSTREAM=gmail`): reads unread mail, and an allowed `send_email` only creates a **draft**. Tests always use a fake Google API; never show a real inbox on the projector without checking what is in it.
7. **Contracts first.** An endpoint or shape changes in `contracts/` first, then `backend/app/contracts.py`, then `frontend/src/lib/api/types.ts`, then tests.
8. **No fake success.** Numbers on screen or in the pitch come from `python -m app.eval_runner` (measured), never typed. No always-passing tests, no TODO stubs on main.
9. **Every policy or rule change has a test** in `backend/tests/` that would fail without it.
10. **Secrets live only in `.env` files** and the host's settings. Never in code, logs, commits or chat. Don't read `.env*` files.
11. **Wording:** never claim "100% secure", "unhackable", "blocks all attacks", "guaranteed". Say the honest limit (docs/THREAT-MODEL.md §5).

## Don't guess
- Before using a library function, CLI flag, config key or version this project hasn't checked, follow the `verify-before-use` skill and write what you confirmed in `docs/API-NOTES.md`. Versions here are new (TypeScript 7, Vite 8, React 19.3, openai SDK 3.x): your memory may be wrong.
- A fact on a slide or in a judge answer must be in `docs/FACTS.md`. Otherwise say "Not verified yet".
- Say what you ran and what you saw ("I ran `make test`: 75 passed").
- If two docs disagree, or the docs and the code disagree, stop and ask.

## Commands (from the repo root)
- `make setup` – create the backend venv and install both halves
- `make backend` – API on http://localhost:8000 (docs at /docs)
- `make frontend` – UI on http://localhost:5173
- `make test` – backend tests · `make eval` – shield OFF vs ON table · `make check` – **lint + tests + typecheck + build for both halves. Must pass before anything counts as done.**
- Without make: see `README.md`.

## How to work
- **One task at a time**, named by its slice id from `docs/ACCEPTANCE.md` (V1-…, V2-A…, S-…). Other ideas go under "Ideas / later" in PROGRESS.md.
- **Plan first** when a change touches more than 2 files (`/task`). Wait for an OK.
- **Small diffs.** Edit, don't rewrite whole files. No refactors outside the task.
- **Done** = `make check` passes, the slice's ACCEPTANCE lines are met, PROGRESS.md updated, committed on a feature branch (`/checkpoint`).
- **Bugs:** find the cause first (`/fix`). After two failed fixes, stop and propose a different approach. Every fixed bug gets one line in LESSONS.md.
- **Context:** `/clear` between tasks; `/handoff` before a break or at ~60% context.
- **Explain for judges:** every teammate must be able to explain every part (`/explain`).

## Skills
| Skill | Use it for |
|---|---|
| `passport-gate` | ANY change to the gate, rules, policy, tools, tracer, scenarios |
| `backend-conventions` | routes, db, config, security middleware, tests |
| `frontend-conventions` | API client, state, components |
| `project-ui` | any screen, component, style |
| `api-contracts` | adding or changing an endpoint |
| `verify-before-use` | before any API, flag, version or fact not yet checked |
| `judge-ready` | before a judge visit or the final pitch |

## Agents
| Agent | When |
|---|---|
| `reviewer` | after a change touching more than 2 files, before merging to main |
| `red-teamer` | after any gate change: tries to get an attack past PASSPORT, reports bypasses as failing tests |
| `contract-auditor` | after changes to contracts/, routes, or `frontend/src/lib/api/` |
| `ui-critic` | after building or changing a screen, before judge visits |
| `test-writer` | when a slice needs tests, after a bug fix |
| `researcher` | when a statement needs a source for FACTS.md |

Slash commands: `/start`, `/task`, `/checkpoint`, `/fix`, `/review`, `/attack`, `/eval`, `/ui-pass`, `/explain`, `/research`, `/handoff`, `/judge`.

## Git
- `main` is the demo. Work on `feat/<slice>` branches; merge only after `make check` passes.
- Small commits: `feat:`, `fix:`, `test:`, `docs:`. Don't push unless asked.
- Never rewrite history (no force-push, amend, rebase). Never commit `.env*` (except `.env.example`), `backend/var/`, `screenshots/`.

## Known gotchas (details in docs/LESSONS.md)
- YAML: `#` after a space starts a comment. Quote any scenario title containing `#` or `:`.
- React effects must use a block body `useEffect(() => { ... })`: an arrow that returns a value crashes ("destroy is not a function").
- `<dialog>.showModal()` throws if already open; StrictMode runs effects twice. Guard with `if (!ref.current.open)`.
- Don't `pkill -f "<pattern>"` from a shell whose own command line contains that pattern: it kills itself.
