# Design: Sky Ink

## 1. The feeling
Calm, editorial, exact. A customs desk printed on good paper, not a hacker movie or a dashboard template. Readable from the back of a hall on a projector.

## 2. Principles
1. **One bold thing per card:** the verdict stamp.
2. **Colour carries meaning only** (verdicts and origins), and every colour also has words.
3. **Restraint over decoration.** White page, near-black ink, 1px lines, almost no shadows.
4. **One blue action per view.** `--sx-blue` is only for the main action (Run scenario, Run evaluation, Verify chain, Retry). Everything else is an ink pill, an outlined pill or a text link.
5. **One sky block per page** (`--sx-sky`) for the feature moment: the request and Run on Agent, the metrics on Scoreboard.
6. **Yellow is a highlighter, not a colour.** It marks text that came from outside, a phrase in a headline, an "Attack" tag, or an illustration accent. It is never a button or a large fill.
7. **Every state is designed:** idle, starting, running, waiting for approval, done, error, backend unreachable, empty.

## 3. Signature element
The **passport stamp** on every decision card: ALLOWED (green ink), NEEDS YOU (amber ink), DENIED (red ink). It has a double ring (2px border plus an inset 1px outline), is rotated -3°, and presses in over 200 ms. With the shield off it becomes a dashed grey "Would deny / Would ask" stamp plus a red-ink "Shield off: it ran" pill. The stamp is the only ALL-CAPS text in the UI.

## 4. Tokens (`frontend/src/styles/tokens.css`)
**Layer 1, Sky Ink primitives (`--sx-*`):**
- page #FFFFFF · ink #0A0A0A · mute #52525B · subtle #71717A (text on white only)
- line #E4E4E7 · field-line #D4D4D8 · soft #F4F4F5 · panel #EEF6FF · sky #CFE6FF
- blue #2563EB / hover #1D4ED8 · ring #93C5FD · marker #FFE45C

**PASSPORT exception:** three printed-ink verdict colours: ok #166534, warn #92400E, bad #B91C1C. Each is ≥ 5:1 on page, panel, sky and marker. Use them only in stamps, result numbers, yes/no cells and the attacker alert. See DECISIONS.md, 2026-10-31.

**Layer 2, semantic (`--color-*`):** what app.css uses. Components never use a raw value.

**Origins** (where a value was born). The value itself carries the treatment, and the words always appear next to it:
| Origin | Treatment |
|---|---|
| From you | panel fill + 2px ring-blue underline |
| Trusted registry | plain |
| Outside content | **yellow highlighter**: the same yellow marks the attacker's line in the evidence document |
| Secret | **black redaction bar**, white text |
| Written by the AI | dashed underline |

**Type:**
- **Newsreader 500** (self-hosted, OFL, optical sizing) for display, headings, step numerals, metrics and the wordmark. Letter-spacing -0.02em, line-height 1.05–1.15.
- **Geist** 400/500/600 for everything you read or click.
- **Geist Mono** for tool names, argument values and hashes.
- Tabular numerals on every number.
- Scale: 13 / 14 (code) / 15 / 17 / 22 / 28 (dialog) / 32 / 40 (numeral) / 48 / 64. 13px is the floor.

**Shape:** pills (999px) for everything clickable, tags and status; 16px for surfaces; 12px for inputs and inset panels; 6px for the stamp only. Spacing uses only 4 / 8 / 12 / 16 / 24 / 32 / 48 / 64. Fonts are self-hosted in `frontend/public/fonts/`, never loaded from the network.

## 5. Screens (`design/mockups/` holds screenshots of the Sky Ink build)
| Screen | Mockup | Goal | Hierarchy |
|---|---|---|---|
| Agent, shield on | 01-agent-shield-on.png | see each tool call judged | sky hero (request, frozen intent, Run) → route strip → card: stamp → headline → ruled values with origins → rule pills → Show evidence; outcome rail on the right |
| Agent, shield off | 02-agent-shield-off.png | see the attack land | red-ink attacker card in the rail → "Would deny" stamps |
| Evidence | 03-evidence.png | see the exact source line | document sheet, highlighted line, "Hidden in the original email" |
| Approval | 04-approval.png | decide in 5 seconds | risky values with origins → why → Reject (ink, focused) / Approve (outline) |
| Scoreboard | 05-scoreboard.png | proof | serif headline with "Fails after." highlighted → metrics in the sky block → table |
| Audit | 06-audit.png | tamper evidence | headline → chain status pill → ruled table |

**Idle Agent:** a serif headline with the line-art passport, the sky hero, then the scenario list. Scenarios are ruled rows with a radio, never a grid of floating cards.

**During a run** the hero tightens (request at 22px, controls in two rows) so the cards sit higher at 1280×720.

**Backend down** is a full illustrated page with Retry, not a banner.

## 6. Motion
- 200 ms for state changes: a card rises 8px, the stamp presses in from 1.25× after 80 ms, controls change colour.
- 800 ms for scene changes: the intro and pages rise in.
- 2.4–5 s loops only inside illustrations and the "agent is working" dot.
- No count-ups, no shimmer, no 3D, no hover effects beyond colour.
- `prefers-reduced-motion` stops everything.

## 7. Illustrations
Black line art in `components/Illustration.tsx`: passport (idle), unplugged (backend down) and ledger (empty). 1.8px stroke, round caps, white paper fill, one yellow accent each, `aria-hidden`. Add new scenes in the same style; never use emoji or stock icons as illustration.

## 8. Quality checklist
- [ ] Only token colours; one blue action visible per view; no gradients, glass, glow or purple
- [ ] Headings in Newsreader, UI in Geist; pills to click, 16px surfaces, 12px inputs
- [ ] No coloured side borders on cards, no rows of identical floating cards
- [ ] Every origin has its words next to the treatment; contrast ≥ 4.5:1; text ≥ 13px; targets ≥ 44px
- [ ] Focus ring visible; Esc behaviour; reduced motion stops everything
- [ ] Checked at 1440×900, 1280×720 and 360 wide (no horizontal scroll)
