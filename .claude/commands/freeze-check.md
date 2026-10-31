---
description: Pre-freeze status check (run ~11:00): what is missing or not done before the 12:00 code freeze
disable-model-invocation: true
---
Code freeze is 12:00 and submission closes 16:00 on 31 Oct. Tell me what is missing, using evidence. Don't trust ticks alone. **Read-only: don't edit, commit, switch branches or merge anything.**

1. Run `git fetch origin` and note the current time. Everything below is about **origin/main**, because that is what judges see.
2. Read docs/ACCEPTANCE.md sections **J**, **G3**, **G5** and **E-1**, and prompts/J-judge-fixes.md.
3. Verify each J item on origin/main yourself, regardless of its tick:
   - J1: `git grep -n R9_BODY_UNTRUSTED origin/main -- backend/` and `backend/tests/test_body_entities.py` exists on origin/main.
   - J2: `git grep -n -i "approver" origin/main -- backend/app/` (a separate approver code checked on /approvals).
   - J3: `git grep -n -i "hmac" origin/main -- backend/app/db/audit.py`, and `--recompute` in scripts/tamper_audit.py.
   - J4: a negation check in backend/app/gate/capsule.py on origin/main, plus a test.
   - For anything not on main, check whether a branch exists (`git branch -r`, `git log origin/<branch> --oneline -5`) and how far along it looks.
4. Check that main is green. Use `gh run list --branch main --limit 3` if gh works. Otherwise, only if the local checkout is a clean `main` equal to origin/main, run `make check` and `make eval` (Windows without make: the README commands). Compare the eval with docs/RESULTS.md: attacks 9/9 → 0/9, legit 7/7 → 7/7, 0 popups.
5. Check G3 (Gateway tab on main?) and every unticked line in E-1 and G5.

Answer in this shape, short:
- **Time left to freeze:** X min
- **Done on main** (one line each, with the evidence you saw)
- **Missing / not done**, as a table: item · owner · state (not started / branch exists / on branch but not merged / failing) · what to do now
- **Cut list:** what to drop if it can't land by 11:45 (J4 first, then J3; J1 and J2 are must-haves; never merge a red branch to main)
- **Pitch impact:** for each missing J item, the honest one-line answer to use in Q&A instead
