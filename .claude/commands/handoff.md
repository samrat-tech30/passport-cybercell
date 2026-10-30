---
description: Save everything needed to continue later (before /clear, a break, or sleep)
disable-model-invocation: true
---
We're pausing (the context is getting full, a break, or sleep). Make sure nothing is lost:
1. Update docs/PROGRESS.md: exactly what's done, what's half done (which files, what's left), open bugs, and the very next step written as a ready-to-use prompt.
2. Add any new decisions to docs/DECISIONS.md, lessons to docs/LESSONS.md, checked APIs to docs/API-NOTES.md, and sourced facts to docs/FACTS.md.
3. If the work is in a working state, run `make check` and commit. If not, commit to the feature branch with a "wip:" message and say so in PROGRESS.md.
4. Tell me in 3 lines what to type when I come back.
