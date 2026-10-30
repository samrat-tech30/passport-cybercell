# START HERE (team, first 30 minutes)

This repo merges two things: the **Claude Code process kit** from our friend's hackathon starter (hooks, slash commands, review agents, memory docs) and a **working, tested PASSPORT v1** (backend, database, security, UI, 11 attack scenarios, 85 tests). You don't start from zero: you extend it.

## 1. Every laptop (10 min)
1. Unzip, `cd passport`, `git init && git add -A && git commit -m "starter"` (one person pushes to a private GitHub repo; the others clone it).
2. `make setup` → `make backend` + `make frontend` → open http://localhost:5173 → run S2 with the shield off, then on.
3. `make check` must print ALL CHECKS PASSED.
4. Node is needed on every laptop (the Claude Code hooks are `.mjs`).

## 2. Claude Code
- Run `claude` from the repo root. The SessionStart hook loads `docs/PROGRESS.md` + `docs/LESSONS.md` + git state automatically.
- First prompt on each laptop: `prompts/00-first-session.md`.
- Then your role prompt (roles in `docs/PLAN.md`): `prompts/M1-…`, `M2-…`, `M3-…`, `M4-…`.
- Daily loop: plan (Claude asks for your OK) → build → `/checkpoint` → `/review` before merging → `/handoff` before sleep.
- Useful: `/attack <idea>` (new attack scenario), `/eval` (measured numbers), `/explain <file>` (judge prep), `/fix <bug>`.

## 3. Rules that matter most (full list in CLAUDE.md)
- Tools run only through `backend/app/gate/handle.py`. Any error = DENY.
- No numbers on slides except from `make eval` (docs/RESULTS.md).
- All data synthetic, `.test` domains. Never commit `.env`.
- Work on `feat/<slice>` branches; `main` must always demo.

## 4. What changed vs. the friend's starter
| Friend's starter | This repo |
|---|---|
| Generic template, `<fill>` placeholders, no project content | Filled for PASSPORT: spec, threat model, architecture, plan, pitch, facts with sources |
| Empty `backend/` and `frontend/` | Working backend (FastAPI, SQLite, migrations, audit chain, security middleware) and frontend (React + Vite) that deploy separately |
| No tests | 85 backend tests incl. every attack OFF vs ON, contract-shape tests, security tests; `make check` + CI |
| 2-person ownership | 4 roles, timeline, ready prompts per person and per v2 upgrade |
| Mobile-first UI rules, messages file | Projector-first rules; real screenshots as mockups |
| Guard hook: wording, colours, secrets | + PASSPORT invariants (tools only via the gate), unsafe Python (eval, shell=True, f-string SQL, yaml.load), Groq/Google keys, canary values |
| Agents: reviewer, test-writer, ui-critic, contract-auditor, researcher | + **red-teamer** (tries to bypass the gate, reports failing tests); all adapted to this stack |
| — | `/attack` and `/eval` commands, `passport-gate` domain skill |
