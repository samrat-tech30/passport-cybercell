---
name: verify-before-use
description: Anti-hallucination check before using any library function, framework convention, browser API, CLI flag, config option, URL, version number, law, statistic or other fact you have not already confirmed in this project. Use it whenever you are about to write code against an API you have not used here yet, when an error suggests an API mismatch, or when a sentence states a fact.
---

# Check before you use it

Your training data is older than this project's packages and today's rules. A confident guess that's wrong costs the team an hour at 3 a.m. So: **check, then use, then write down what you checked.**

## 1. Is it already confirmed?
- Library and API facts: `docs/API-NOTES.md`.
- API shapes between the halves: `contracts/README.md` (never guess a field name).
- Numbers, laws, quotes, names, URLs: `docs/FACTS.md` (never state a fact that isn't there).
- UI words: `docs/DESIGN.md`.
- Product decisions: `docs/DECISIONS.md`.
If it's there, use it. If it's marked **to check**, check it now.

## 2. How to check code facts (cheapest first)
1. Installed version: `npm ls <pkg>` (in frontend/) or `backend/.venv/bin/pip show <pkg>`; read `node_modules/<pkg>/package.json` (`version`, `exports`, `types`).
2. Installed types or source: search `node_modules/<pkg>/**/*.d.ts`, or the package's source in `backend/.venv/lib/python3.*/site-packages/<pkg>/`. **If it isn't in the installed version, it doesn't exist**, whatever you remember.
3. Framework docs that ship with the package (for example `frontend/node_modules/vite/README.md`).
4. Official docs with WebFetch (the library's own site or repo), not blog posts.
5. Run it: a 10-line script or a test. Running beats reading.

## 3. How to check facts (statistics, laws, people, organisations)
- Use the `researcher` agent. It returns only sourced statements and says "not found" otherwise.
- Add the fact to `docs/FACTS.md` with the link and the date.
- Until then, the app, the pitch and the judge answers don't use it.

## 4. Write it down
Add one line to `docs/API-NOTES.md`: `- <api>: <what is true> (<tested|read>, <pkg@version>, <date>)`. Next session won't have to check again.

## 5. Say what you don't know
When something can't be confirmed from here (a real phone, the venue network, a service's rate limit, the projector), say so plainly:
> **Not verified:** <what>. **How to check:** <exact steps>. **What I assumed meanwhile:** <assumption>.
Never write "this should work" as if it were tested.

## Red flags that mean "stop and check"
- You're about to import something you haven't seen in `package.json` / `pyproject.toml`.
- The error says "is not a function", "has no exported member", "Cannot find module", "AttributeError", "unexpected keyword argument".
- You're adding a config option from memory.
- You're writing a number into the UI or docs (limits, sizes, prices, statistics, dates).
- You're quoting a law, a report or an organisation.
