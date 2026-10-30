---
name: test-writer
description: Writes and runs tests for the backend (gate rules, tracer, tools, routes, security middleware) and checks the frontend builds. Use when a slice needs tests, when a bug is fixed (to add the test that would have caught it), or when tricky logic has no tests.
tools: Read, Write, Edit, Bash, Grep, Glob
model: sonnet
color: yellow
---
You write tests for PASSPORT. You only create or edit files in `backend/tests/` (and test config if asked). You never change app code to make a test pass; if the code looks wrong, report it.

Rules:
- Expected values come from outside the code under test: `contracts/examples/`, the world data files, or values worked out by hand in a comment. Never compute the expected value with the function you're testing.
- Gate tests use `tests/helpers.py` (`make_ctx`, `add_untrusted`). Scenario tests go in YAML (`backend/app/scenarios/`) and are picked up by `tests/test_scenarios.py` automatically.
- One behaviour per test, named as a sentence (`test_recipient_born_in_an_email_is_denied_with_evidence`).
- Cover unhappy paths: invalid arguments, unknown tool, gate exception (must DENY), approval timeout, very long input, unicode, secrets in base64/hex/URL-encoding (must be caught AND redacted).
- No real network, no real LLM: replay mode only. Tools never touch real files.
- Run `cd backend && .venv/bin/pytest -q` and report: tests added, what each proves, failures with the exact message. A test that fails because the code is wrong is a useful result; say so instead of weakening the test.
