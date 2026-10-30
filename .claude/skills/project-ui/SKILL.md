---
name: project-ui
description: Build or change any PASSPORT screen, component or style so it reads instantly on a projector and looks credible, not like generic AI-made UI. Use for every task that touches frontend components, CSS or the look of a page.
---

# PASSPORT UI

The bar: a judge at the back of the hall understands any decision in 3 seconds. That comes from discipline, not decoration.

## Before writing code
1. Read docs/DESIGN.md and **look at the mockup PNG** in `design/mockups/` for that screen (Read tool on the PNG).
2. Find the token you need in `src/styles/tokens.css`. If it doesn't exist, ask; don't invent a colour.

## Rules (system: Sky Ink, details in docs/DESIGN.md)
- **Colour = meaning only.** White page, ink text. Verdict inks: ok (green) allow, warn (amber) needs you, bad (red) deny. Use them only in stamps, result numbers, yes/no cells and the attacker alert.
- **Origins** are drawn on the value itself:
  - from you: panel fill + blue underline
  - trusted: plain
  - outside content: yellow highlighter
  - secret: black redaction bar
  - written by the AI: dashed underline

  The origin words always sit next to the value. No purple, no orange.
- **One blue action per view** (`btn--brand`). Everything else is `btn--ink`, `btn--outline` or a text link.
- **One sky block per page** (the Agent hero, the Scoreboard metrics). Never use sky for small cards.
- **Yellow is a highlighter:** headline phrase (`.hl`), outside-content values, "Attack" tag, illustration accent. Never a button or a big fill.
- **One bold thing per card:** the stamp (double ring, rotated -3°, presses in over 200 ms, none under reduced motion). Shield-off cards get a dashed grey "Would deny/ask" stamp, never the coloured one.
- **Type:** Newsreader 500 for display, headings, step numerals and metrics; Geist for everything you read or click; Geist Mono for tool names, values and hashes. Text 15px, small 13px minimum (projector). Tabular numbers everywhere.
- **Shape:** pills for anything clickable, tags and status; 16px surfaces; 12px inputs and inset panels; 1px lines. The only shadow is the dialog lift.
- **Spacing** only from the scale (4, 8, 12, 16, 24, 32, 48, 64).
- **Every state:** idle (intro + scenario list), starting, running, waiting for approval, done, error, backend unreachable (illustrated page), empty (illustrated).
- **Illustrations:** black line art in `components/Illustration.tsx` (1.8px stroke, one yellow accent, `aria-hidden`). No emoji, no stock icons as art.
- **Accessibility:** focus ring visible, buttons are `<button>`, the shield toggle is `role="switch"`, the live timeline has `aria-live="polite"`, dialogs labelled, Reject focused in the approval dialog, 44px targets.

## Screenshot loop (before saying a UI task is done)
1. `make backend` + `make frontend` running.
2. `node frontend/scripts/screenshot.mjs / --run s2` and `--projector`. Files land in `screenshots/`.
3. Read the PNGs, compare with the mockups, fix, re-shoot. Bigger changes: ask the `ui-critic` agent.

## Anti-slop (any yes is a bug)
Decorative gradient/glow/glass · purple · emoji · ALL CAPS except the stamp · **a coloured border down one side of a rounded card** · **a row of identical floating cards** (use ruled lists, or one sky block with 1px dividers) · boxed chips around every value · more than one blue button in view · more than one bold thing per card · Inter or system-font default look · fake numbers · words like "seamless", "AI-powered", "unhackable" · hover effects on everything · layout shift when events arrive.
