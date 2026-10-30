---
name: api-contracts
description: Add or change a PASSPORT API endpoint or shape - contract-first order, snake_case fields, the error format, examples, the CHANGELOG, and keeping backend/app/contracts.py and frontend/src/lib/api/types.ts in sync. Use whenever a task adds an endpoint, changes a field, status code or event type.
---

# Changing the API, contract first

`contracts/` is the only source of truth for what crosses between `frontend/` and `backend/`.

## The order (never skip a step)
1. Propose the change in the plan (endpoint, fields, errors); get a yes from the frontend and backend owners.
2. Edit `contracts/README.md`.
3. Add/update an example in `contracts/examples/<name>.json` (`request` + `response.status` + `response.body`).
4. Add a line to `contracts/CHANGELOG.md` (date, what, why, who agreed).
5. Backend: `app/contracts.py` / `app/api/schemas.py` / route + a test. `tests/test_contract_examples.py` checks examples against real responses.
6. Frontend: `src/lib/api/types.ts` + `client.ts`.
7. Run the `contract-auditor` agent. Optional: `make openapi` regenerates `contracts/openapi.json`.

## Conventions
- JSON fields **snake_case**. Times are Unix seconds (float). Money is whole rupees (`amount_inr`, int). IDs are strings with a prefix (`ses_`, `dec_`, `eval_`).
- Errors: `{"error": {"code": "snake_case_code", "message": "plain words"}}` with the right status.
- Secrets never appear in any response; values are redacted to `[secret:NAME]`.
- Add a field rather than rename one.
