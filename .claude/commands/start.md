---
description: Start a work session - read memory, report status, propose the next step
disable-model-invocation: true
---
Start of a work session.
1. PROGRESS.md, LESSONS.md and git state are already in context from the session-start hook. Also read CLAUDE.md's rules if you haven't this session.
2. Check `git status` and the current branch.
3. Tell me in at most 6 lines: where we are, what's in progress, open bugs, and the next task you propose (with its slice id from docs/ACCEPTANCE.md and the matching file in prompts/).
4. Don't write any code yet. Wait for my go.
