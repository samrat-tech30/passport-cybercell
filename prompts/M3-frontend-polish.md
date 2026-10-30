I'm M3 and I own the frontend. Slice V1-3 polish (docs/ACCEPTANCE.md).

Read first: CLAUDE.md, frontend/CLAUDE.md, the project-ui and frontend-conventions skills, docs/DESIGN.md, and LOOK at every PNG in design/mockups/.

Plan first and wait for my OK. Then, one at a time, with the screenshot loop after each (`node frontend/scripts/screenshot.mjs / --run s2`, `--off`, `--projector`; install playwright in frontend as a dev dependency if missing, ask me first):
1. Projector pass at 1280×720: the three columns must fit; if not, collapse the left column into a compact header strip. Text never below 13 px.
2. States: backend unreachable (banner + "Retry" button), session error, empty attacker panel, run finished. All readable.
3. Decision cards: long values must not overflow; the "Show evidence" button stays on the right; non-sink args (subject/body) visually quieter than sink args.
4. A small legend under the top bar explaining the origin colours in words (from you / trusted / outside content / secret / written by the AI). Only 5 items, one line.
5. Scoreboard: after a run, highlight in one sentence what the table proves ("Shield on: 0 of 7 attacks got through, 6 of 6 legit tasks still done") built from the API numbers, never typed.
6. Keyboard: Tab order sensible, Enter on "Run scenario", Esc closes the evidence drawer and rejects the approval.

Then run the ui-critic agent and fix its must-fix items. Don't touch backend/ or contracts/. `npm run check` must pass.
