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
- No `sqlite3` CLI on most laptops (Windows) → tamper demo is a Python script: `make tamper`.
- A test failed about 1 run in 4 (amount 2 traced to SECRET) → the tracer looked for the value INSIDE random hex canaries → a value is secret-born only if it contains the whole secret.
- A 900-space email line took 5 s in decide() → `\s*[\[(]?\s*\bat\b` backtracks cubically on long whitespace → collapse whitespace before regexes with adjacent `\s*`.
- "ignore anyone at evil.test" in the user's request made anyone@evil.test look user-typed → a disguise/squash pass over user/trusted text can grant trust → disguised matches may only take trust away, never grant it.
- `mktemp` ignored TMPDIR on macOS → BSD mktemp with no template uses the system temp dir → `mktemp "${TMPDIR:-/tmp}/name.XXXXXX"`.

- s9b/s13b only got ASK → email fields other than From/Subject/body were never added to the untrusted segment → label every field except id/from/subject/body, after the body.
- Zero-width address in a nested email field only got ASK → str() of a dict/list uses repr(), which writes U+200B as the text "​" → walk nested values down to raw strings.
- Email without a subject crashed the session → `e['subject']` KeyError in ingest → read optional mail fields with `.get()`.
- Evidence card showed the wrong line → line number counted with "\n" but snippet picked from splitlines() (also splits on U+2028, \r) → one `split_lines` helper everywhere.
