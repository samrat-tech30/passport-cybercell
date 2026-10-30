---
name: project-ui
description: Build or change any PASSPORT screen, component or style so it reads instantly on a projector and looks credible, not like generic AI-made UI. Use for every task that touches frontend components, CSS or the look of a page.
---

# PASSPORT UI

The bar: a judge at the back of the hall understands any decision in 3 seconds. That comes from discipline, not decoration.

## Before writing code
1. Read docs/DESIGN.md and **look at the mockup PNG** in `design/mockups/` for that screen (Read tool on the PNG).
2. Find the token you need in `src/styles/tokens.css`. If it doesn't exist, ask; don't invent a colour.

## Rules
- **Colour = meaning only.** Verdicts: ok (green) allow, warn (amber) needs you, bad (red) deny. Origins: blue from you, grey trusted, orange outside content, purple secret, dashed border written by the AI. Brand blue only for the main action and focus. Never colour alone: every chip also says its origin in words.
- **One bold thing per card:** the stamp. The signature element is the passport stamp (slightly rotated, lands with a 260 ms scale animation, none under reduced motion). Shield-off cards get a dashed grey "Would deny/ask" stamp, never the coloured one.
- **Type:** text 15 px, small 13 px minimum (projector), titles 18, display 28. Mono for tool names, argument values, hashes. Tabular numbers for counts and times.
- **Spacing** only from the scale (4, 8, 12, 16, 24, 32, 48). Radius by role (cell 6, control 8, card 12).
- **Every state:** idle (invite to pick a scenario), starting, running, waiting for approval, done, error, backend unreachable.
- **Accessibility:** focus ring visible, buttons are `<button>`, the shield toggle is `role="switch"`, the live timeline has `aria-live="polite"`, dialogs labelled.

## Screenshot loop (before saying a UI task is done)
1. `make backend` + `make frontend` running.
2. `node frontend/scripts/screenshot.mjs / --run s2` and `--projector`. Files land in `screenshots/`.
3. Read the PNGs, compare with the mockups, fix, re-shoot. Bigger changes: ask the `ui-critic` agent.

## Anti-slop (any yes is a bug)
Decorative gradient/glow/glass · emoji · ALL CAPS except the stamp · more than one bold thing per card · fake numbers · words like "seamless", "AI-powered", "unhackable" · hover effects on everything · layout shift when events arrive.
