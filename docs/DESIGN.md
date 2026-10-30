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
CSS only, tokens in tokens.css. Allowed: a decision card slides up 8 px as it arrives (320 ms), then its stamp lands (260 ms spring, 140 ms later); dialogs rise in (280 ms); the tab plate and the shield knob glide; scoreboard numbers count up once; the attacker panel's check mark draws. Buttons answer a click in 180 ms. The one 3D element is the WebGPU guilloché seal in the idle state (before the first run only; 2D canvas fallback; unmounted during a run). `prefers-reduced-motion` → no animation, seal as a still frame.

## 7. Quality checklist
- [ ] Matches mockups at 1440×900 and 1280×720
- [ ] Guard hook passes (tokens only)
- [ ] All states reachable
- [ ] Focus ring visible; contrast ≥ 4.5:1; text ≥ 13 px
