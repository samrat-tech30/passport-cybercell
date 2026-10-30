# Lessons (mistakes not to repeat)

> Claude: read this every session. When a bug is fixed, add one line: symptom → cause → fix. Keep it under 120 lines.

- Scenario title showed "Hidden instruction in Email" without "#3…" → in YAML ` #` starts a comment → quote every scenario title.
- Evidence drawer crashed with "destroy is not a function" → `useEffect(() => el.scrollIntoView())` returned a value (newer Chromium returns one from scrollIntoView) → always use block bodies in effects.
- Dialogs can throw on a second `showModal()` (StrictMode runs effects twice) → guard with `if (!ref.current.open)`.
- UI test clicked the wrong button → the tab and the action button were both labelled "Run" → unique labels ("Agent" tab, "Run scenario" button).
- "Summarise my unread emails" unlocked send_email → the word "email" mapped to sending → reading words unlock reading only; an address or "send/reply/forward" unlocks sending.
- `pkill -f "uvicorn app.main:app"` killed the shell running it → the pattern matched the shell's own command line → kill by PID (`ps aux | grep …`), or match a narrower pattern.
- At 1280×720 argument values wrapped one letter per line → the long origin label was `nowrap` in a 3-column grid → container query: origin goes under the value on narrow cards.
- Screenshot script timed out → Playwright can't mix `text=` and CSS in one comma selector → CSS only (`p.done, dialog.approval[open], p.error`).
- Files flipped to CRLF after a scripted edit on Windows → Python `Path.write_text` translates `
` to `
` → write with `write_bytes(text.encode())` or `newline="
"`.
- `scripts/check.sh` fails on Windows (`.venv/bin` doesn't exist; it's `.venv/Scripts`) → run its steps by hand with `Scripts/` paths.
- No `sqlite3` CLI on most laptops (Windows) → tamper demo is a Python script: `make tamper`.
