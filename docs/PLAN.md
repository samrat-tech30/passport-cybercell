# Plan: roles, order, timeline

The v1 core is already built and tested. Tonight is about: (1) a live LLM that really falls for the attack, (2) one or two v2 upgrades that make us different, (3) a polished, rehearsed demo. Don't rebuild what works.

## Roles
| Person | Owns | First prompt | v2 piece |
|---|---|---|---|
| **M1 Agent + API** | live LLM mode, replay recordings, API, deploy | `prompts/M1-live-llm.md` | E MCP gateway (replaces D, `prompts/GATEWAY-PROMPTS.md`) |
| **M2 Gate** | rules, tracer, policy, tests | `prompts/M2-gate-v2-disguise.md` | B disguise-proof tracing |
| **M3 Frontend** | UI polish, projector, two-window view, scoreboard | `prompts/M3-frontend-polish.md` | C two-window view |
| **M4 Attacks + story** | new attack scenarios, UPI world, threat model, slides, video | `prompts/M4-attacks-and-story.md` | A UPI payments; C threat ledger |

## Order of v2 work (cut from the bottom if late)
1. **B disguise-proof tracing** (M2) – turns s7b/s7c from ASK into DENY; Indian-language angle.
2. **A UPI payments + mandate lock** (M4 + M2) – the India story (agentic UPI payments).
3. **C herd immunity** (M4 + M3) – the memorable two-window moment.
4. **E MCP gateway** (M1 / Person B, `prompts/GATEWAY-PROMPTS.md`, slices G0–G5; supersedes v2-E) – replaces D: the problem statement names "MCP gateway" as an extension; outside agents go through the gateway, a fake upstream MCP server does the work, the dashboard is the control panel. Start by 04:00; cut at 08:00 if not working.
5. **D payment visa** – dropped; only if everything else is done.
Never cut: v1 gate, evidence drawer, before/after demo, scoreboard.

## Timeline (IST)
| Time | Work | Checkpoint |
|---|---|---|
| 19:45–20:15 | Everyone: `make setup`, run the demo locally, read CLAUDE.md + their prompt. M1 tests live LLM providers. | CP0 20:15: every laptop runs S2 off/on |
| 20:15–21:00 | Dinner + 10-min standup | |
| 21:00–00:30 | M1 live LLM + recordings · M2 v2-B · M3 projector polish + states · M4 new attacks + UPI world + threat-model slide | CP1 00:30: live LLM decision made; v2-B tests green |
| 00:30–04:00 | M2+M4 v2-A · M3 payments panel + two-window view · M1 deploy backend + frontend | CP2 04:00: v2-A green, deployed URL works |
| Sleep | M4 01:30–04:30 · M1+M2 04:00–07:00 · M3 naps after breakfast | |
| 04:00–08:00 | v2-C (M4 ledger, M3 UI) · M1 D if ahead · re-record replays | CP3 08:00: full demo from the UI, `make check` green |
| 08:00–09:00 | Breakfast | |
| 09:00–12:00 | No new features. Fix bugs, RESULTS.md, README, slides, 2-min backup video, `/explain` each part | CP4 12:00: **code freeze**, tag `v1.0`, rehearse ×3 |
| 13:00–14:00 | Lunch | |
| 14:00–14:30 | **Submit** (repo, video, slides). Deadline 16:00. | |

Rule: >45 min behind at a checkpoint → cut scope, not sleep.
