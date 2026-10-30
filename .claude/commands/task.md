---
description: Plan one build slice or task before coding
argument-hint: <slice id or task, e.g. "P2 login" or "E1 dashboard">
disable-model-invocation: true
---
Task: $ARGUMENTS

1. Read docs/PROGRESS.md, the slice's checks in docs/ACCEPTANCE.md, and only the sections of docs/SPEC.md, docs/ARCHITECTURE.md and contracts/README.md that this task needs.
2. Name the skills you'll follow (passport-gate for anything in backend/app/gate, tools or scenarios; backend-conventions, frontend-conventions, project-ui, api-contracts, verify-before-use) and read them.
3. Say which half or halves this touches (frontend, backend, contracts). If it needs a contract change, the plan starts with that change and needs both people's yes.
4. If we're on main, propose a branch name (`feat/p2-login`).
5. Write a short plan: the files to create or change, the steps, the tests you'll add, the acceptance checks you'll meet, and how we will check it by hand (UI at localhost:5173, make eval). List anything you're unsure about (and how you'll verify it), and any new dependency with why.
6. Keep the scope to this task. Anything else goes under "Ideas / later" in PROGRESS.md.
7. Stop and wait for my OK before writing code.
