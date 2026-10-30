---
description: Verify, record progress and commit after a finished step
disable-model-invocation: true
---
Finish this step properly:
1. Run `make check` (ruff + pytest + typecheck + build for both halves). If anything fails, stop and show me the error; don't commit.
2. If the step touched `backend/app/gate/`, `tools/`, `policy.yaml` or scenarios: run `make eval` and compare with the numbers in docs/RESULTS.md. Attacks landed with shield ON must stay 0 and legit tasks completed must not drop. If they changed, tell me before committing.
3. Check the diff for: secrets or canary values, fake numbers, TODO stubs, debug prints, a tool called outside `gate/handle.py`, an exception path that could ALLOW, contract drift, and breaks of the CLAUDE.md rules. Tell me about anything you find.
4. Tick the slice's lines in docs/ACCEPTANCE.md that are now true; list the ones that need a manual test.
5. Update docs/PROGRESS.md (done, in progress, known bugs, next task, last updated). Keep it under 150 lines.
6. Add a row to docs/AI-LOG.md (what you did; leave "What the human did" for me unless I told you).
7. If a bug was fixed, a line in docs/LESSONS.md. If an API was checked, docs/API-NOTES.md. If something was decided, docs/DECISIONS.md.
8. Commit on the feature branch with a clear message (`feat:`, `fix:`, `test:`, `docs:`). Don't push unless I ask.
9. Tell me exactly what to test by hand before merging to main.
