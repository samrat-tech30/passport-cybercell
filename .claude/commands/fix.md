---
description: Structured debugging - find the cause before changing code
argument-hint: <what went wrong, error text>
---
Problem: $ARGUMENTS

Follow this protocol:
1. Restate the problem in one line. Say whether it's in the frontend, the backend or between them (check the request and response against contracts/). Check docs/LESSONS.md for a similar earlier bug.
2. List the 2–3 most likely causes, most likely first.
3. For each, say how to confirm or rule it out (a log line, a small pytest, the browser network tab, `curl -s http://localhost:8000/...`, the audit log).
4. Add the smallest logging or test needed to confirm the cause. Don't change behaviour yet.
5. Only once the cause is confirmed: make the smallest fix, add a test that would have caught it, and run `make check`.
6. Add a line to docs/LESSONS.md: symptom → cause → fix.
If this is the second failed fix for the same problem, stop and suggest a different approach instead of another patch.
