# Design

## 1. The feeling
Calm, exact, credible. A customs desk, not a hacker movie. Readable from the back of a hall on a projector.

## 2. Principles
1. One bold thing per card: the verdict stamp.
2. Colour carries meaning only (verdicts and origins), and every colour also has words.
3. Restraint over decoration.
4. Every state is designed (idle, running, waiting for approval, done, error, backend unreachable).

## 3. Signature element
The **passport stamp** on every decision card: ALLOWED (green), NEEDS YOU (amber), DENIED (red), slightly rotated, lands in 260 ms. With the shield off it becomes a dashed grey "Would deny / Would ask" stamp plus a red "Shield off: it ran" tag.

## 4. Tokens
`frontend/src/styles/tokens.css`. Dark canvas, one brand blue. Origins: blue from you · grey trusted registry · orange outside content · purple secret · dashed border written by the AI. Fonts: **Geist** (text) and **Geist Mono** (tool names, values, hashes, the stamp), self-hosted in `frontend/public/fonts/` (SIL OFL): no network fonts, so venue Wi-Fi can't break them. Warm graphite surfaces, not blue-black. One line under the top bar (Agent tab) explains the origin colours in words.

## 5. Screens (mockups in `design/mockups/`, real screenshots of the starter)
| Screen | Mockup | Goal | Hierarchy |
|---|---|---|---|
| Agent, shield on | 01-agent-shield-on.png | see each tool call judged | stamp → origin chips → one-sentence reason → rules → evidence button |
| Agent, shield off | 02-agent-shield-off.png | see the attack land | red attacker panel → "would deny" stamps |
| Evidence drawer | 03-evidence.png | see the exact source line | highlighted line + "Hidden in the original email" |
| Approval | 04-approval.png | decide in 5 seconds | the risky values with origins → why → Reject (focused) |
| Scoreboard | 05-scoreboard.png | proof | three metrics → per-scenario table |
| Audit | 06-audit.png | tamper evidence | chain status pill → rows |

## 6. Motion
Purposeful only (CSS, tokens in tokens.css): a new decision card fades up 4 px (200 ms); its stamp presses in from 1.15× (180 ms, no overshoot); gate-strip nodes change colour (200 ms); the evidence line flashes once (600 ms); dialogs fade (150 ms). No 3D, no count-ups, no shimmer. `prefers-reduced-motion` → none. Light theme by default (projectors), dark theme via the top-bar toggle. The gate strip (request → agent → PASSPORT check → tool) and plain-English card headlines explain the product before any rule ID.

## 7. Quality checklist
- [ ] Matches mockups at 1440×900 and 1280×720
- [ ] Guard hook passes (tokens only)
- [ ] All states reachable
- [ ] Focus ring visible; contrast ≥ 4.5:1; text ≥ 13 px
