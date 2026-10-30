---
description: Get an independent review of recent changes
---
Review the changes on this branch (`git diff main...HEAD`, or the last commit if on main):
- Always: the `reviewer` agent, against CLAUDE.md, docs/SPEC.md and docs/SECURITY.md.
- If the diff touches `backend/app/gate/`, `backend/app/tools/`, `policy.yaml` or scenarios: also the `red-teamer` agent.
- If the diff touches `contracts/`, `backend/app/api/` or `frontend/src/lib/api/`: also the `contract-auditor` agent.
- If the diff touches components or styles: also the `ui-critic` agent on the Agent tab.
Run them in parallel. Summarise their findings for me, worst first, merged and without duplicates. Don't change any code until I say which ones to fix.
