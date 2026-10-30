---
name: judge-ready
description: Prepare for a judge visit or the final pitch of Parallax 2026 - the 8 criteria and where our evidence is, the 3-minute demo order, the pre-demo checklist, honest answers from FACTS.md, and the judge log. Use before each visit, when writing the /judge update, or when asked how to explain or demo something.
---

# Judge-ready

**Deadline:** submissions close 16:00, 31 Oct 2026 (strict). Code freeze 12:00. Demo from `main`. Pitch script: `docs/PITCH.md`. Measured numbers: `docs/RESULTS.md` only.

## Criteria → our evidence
| Criterion | Our answer (and where to show it) |
|---|---|
| 01 Threat relevance | Indirect prompt injection is OWASP LLM01; EchoLeak and Invariant's MCP tool poisoning (FACTS.md). Threat model slide (docs/THREAT-MODEL.md). |
| 02 Verified effectiveness | Live: S2 shield OFF → key in attacker panel; shield ON → DENY with Email #3 line highlighted. Scoreboard tab: measured OFF vs ON table. `pytest` proves it per scenario. |
| 03 Technical implementation | Deterministic gate, per-argument provenance, canaries, fail-closed, hash-chained audit, 75+ tests, strict API with security headers, rate limits, access code. |
| 04 Innovation | Decides per argument (the legit part keeps working); evidence line shown to the user; plus whichever v2 upgrades are done (UPI mandate lock, disguise-proof tracing in Hindi/Kannada, herd immunity, payment visas). Credit CaMeL/FIDES/PACT. |
| 05 UI/UX | Passport stamp, origin-coloured chips with words, evidence drawer revealing hidden text, approval shows only the risky values. |
| 06 Responsible engineering | All data synthetic, `.test` domains, tools in memory, random canaries, secrets redacted everywhere, no keys in repo. |
| 07 Feasibility & impact | Drop-in `POST /v1/decide` for any framework; India is piloting AI agents that pay with UPI (FACTS.md). |
| 08 Presentation | PITCH.md, rehearsed 3 times with a timer; everyone can explain every part (`/explain`). |

## 30 minutes before a visit
1. `git status` clean on `main`; `make check` green; `make eval` matches RESULTS.md.
2. Start backend + frontend on the demo laptop (or open the deployed URL). Run S2 off/on once.
3. Replay mode selected (no Wi-Fi dependence). Backup video ready on the desktop.
4. Audit tab shows "Chain intact". Have `make tamper` ready in a terminal (PITCH.md).
5. Battery, brightness, Do Not Disturb, other tabs closed.

## Say the limit before they ask
"PASSPORT checks where values came from, not what text means. It won't stop a misleading summary, and in v1 a disguised address goes to your approval instead of being blocked outright."

## After the visit
Write questions in `docs/JUDGE-LOG.md` immediately; turn each into a task or an honest answer.
