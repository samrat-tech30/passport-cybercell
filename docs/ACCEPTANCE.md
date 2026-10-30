# Acceptance: what "done" means for each slice

`[auto]` = covered by a test or `make check`; `[hand]` = checked by a person (write who and when).
Slices marked ✅ were delivered by the starter and verified on 2026-10-30 (85 backend tests, eval 7/7 → 0/7).

## V1-0 Setup (everyone, first 30 min)
- [ ] [hand] `make setup` works on every laptop; `make backend` + `make frontend` show the UI with scenarios
- [ ] [hand] Live LLM key added to `backend/.env` on at least one laptop; `GET /health` shows `live_llm_available: true`
- [ ] [hand] Repo pushed to GitHub (private until submission); CI green

## V1-1 Core gate ✅
- [x] [auto] Tracer: user wins ties, secrets before untrusted, line numbers, amounts with commas (test_tracer.py)
- [x] [auto] Rules R0–R8 each have a unit test (test_decide.py)
- [x] [auto] Every scenario: attack lands OFF, fails ON; legit part still works ON (test_scenarios.py)
- [x] [auto] Secrets never reach DB, audit, events or API (test_scenarios.py, test_api.py)

## V1-2 API + security ✅
- [x] [auto] Contract examples match live responses (test_contract_examples.py)
- [x] [auto] Headers, 413, 429, 401 access code, CORS allowlist (test_api.py)
- [x] [auto] SSE stream delivers events and ends with `done`; approvals resume the agent

## V1-3 UI ✅ (polish is M3's slice)
- [x] [hand] S2 off/on, evidence drawer, approval, scoreboard, audit verified in Chromium 1440×900 (design/mockups/)
- [ ] [hand] Projector check at 1280×720 on the real demo laptop + projector
- [ ] [hand] Backend-down state shows a readable banner

## V1-4 Live LLM (M1)
- [x] [hand] Chosen provider + model call tools reliably for S1 (5 runs in a row) (Groq openai/gpt-oss-120b: 5/5 with each persona, 2026-10-30)
- [x] [hand] With the shield OFF, the live model falls for S2 at least once in 3 runs (or we say honestly that it refuses, and demo in replay) (full leak 2/9 runs, secret read 9/9; not reliable, so S2 shield OFF is demoed in replay: DECISIONS.md)
- [x] [auto] Recorded live runs saved as replay fixtures; replay reproduces them (tests/test_live_llm.py)
- [x] [auto] Live mode errors (timeout, bad JSON args) end in R0 DENY or a clean `error` event, never a hang (tests/test_live_llm.py; 429 → one retry)

## V2-A UPI payments + mandate lock (prompts/v2-A-upi-payments.md)
- [ ] [auto] U1 legit order ALLOW; U2 review redirects payee DENY (R9 + R10); U3 PIN request DENY (R1); U4 "verify ₹10" DENY (R9)
- [ ] [auto] OFF vs ON in eval; payments panel in UI
## V2-B Disguise-proof tracing (prompts/v2-B-disguise-proof.md)
- [x] [auto] s7b and s7c become DENY with the line shown; Kannada/Devanagari digits and look-alike letters covered; 3 false-positive tests pass
## V2-C Herd immunity (prompts/v2-C-herd-immunity.md)
- [ ] [auto] value blocked in session A → R12 in session B; same poisoned email quarantined before B's LLM sees it
- [ ] [hand] two-window demo works
## Gateway (prompts/GATEWAY-PROMPTS.md; replaces V2-E and V2-D)
### G1 Gateway sessions in the backend (Person A)
- [x] [auto] tests/test_gateway_api.py green, each fails without the code: no token env → 503, wrong token → 401; s2 flow over HTTP (list ALLOW, attacker send DENY R3 with the email line, Priya send ALLOW (the data's legit recipient)); decide before intent → 409, second intent → 409; observe for a DENY'd decision → 409, observe twice → 409, the caller can't choose the trust label; observed secret then send_email with it → DENY (R4 or R2); REQUIRE_APPROVAL approved in time → run=true, no answer → run=false with approval "timeout"; two sessions never affect each other's verdicts; shield_on=false → run=true with verdict still DENY; decide raising → run=false, R0
- [x] [auto] contract examples regenerated for the new endpoints; `make check` green
- [x] [auto] `make eval` unchanged (attacks 9/9 → 0/9, legit 7/7 → 7/7, 0 popups)
- [x] [hand] red-teamer run on the gateway routes, findings fixed before merging (5 bypasses → tests/test_redteam_gateway.py, all fixed)
### G2 Fake upstream + gateway + fooled agent (Person B)
- [x] [hand] `fooled_agent.py` runs end to end against the real backend (no stub needed: G1 landed first)
- [x] [auto] the gateway's stdout carries only MCP protocol traffic (start-up test + live stdio run)
- [x] [auto] `nimbus_mcp` refuses to start without `NIMBUS_GATEWAY_KEY`
- [x] [auto] `make check` green
### G3 "Gateway" tab in the dashboard (Person A)
- [ ] [hand] Gateway tab: connected agents (poll 3 s, empty state with commands), live decisions of the selected session, approval center with countdown and the timed-out message; Agent, Scoreboard and Audit tabs unchanged
- [ ] [hand] screenshot loop (desktop + `--projector`) with a `make fooled-agent` session, then ui-critic
- [ ] [auto] `make check` green
### G4 Real end-to-end + Claude Desktop (Person B)
- [x] [auto] integrations/tests/test_e2e.py (4 real stdio+uvicorn tests: s2 with only Priya executed, monitor mode, intent lock + read_secret R1, backend down; garbage/500, unknown tool, key, nimbus without key are covered in-process in test_gateway.py; ~30–36 s on Windows, not under 30) under 30 s against the real backend, each fails without the code: s2 story (only Asha in sent mail); tool before start_task and second start_task refused; backend stopped, garbage or 500 → refused, upstream never called; unknown tool refused; read_secret → DENY R1; nimbus_mcp without key refuses to start; the key never reaches the agent; PASSPORT_SHIELD=off → attacker send goes through, decision still DENY
- [x] [hand] integrations/README.md (setup Windows + macOS, Claude Desktop config with no upstream credential, Inspector command, demo script, honest limits)
- [ ] [hand] tried in Claude Desktop; what really happened written in docs/AI-LOG.md
- [x] [auto] docs/RESULTS.md "Gateway" table filled only from the e2e run output; `make check` green
### G5 Red-team, review, pitch (both)
- [ ] [hand] red-teamer on integrations/ and app/api/gateway_routes.py (skip /decide, observe abuse, approval reuse, token leaks, session crossover, malformed MCP args, upstream output posing as PASSPORT); every bypass a failing test first, then a fix
- [ ] [hand] reviewer on the diff since main@G0; blocking findings fixed
- [ ] [hand] PITCH.md + slides updated with numbers only from `make eval` and the gateway e2e run; `99-demo-prep.md` done
## V2-D Payment visa (prompts/v2-D-payment-visa.md; dropped for the gateway, only if everything else is done)
- [ ] [auto] direct tool call without visa, edited args, reused visa, expired visa → all refused; approved flow still pays

## E-1 Demo ready (by 12:00)
- [ ] [hand] PITCH.md rehearsed 3 times under 3:00
- [ ] [hand] Backup video recorded (2 min) and on the laptop desktop
- [ ] [auto] `make check` green on `main`; RESULTS.md matches `make eval`
- [ ] [hand] Submitted by 14:30 (repo, video, slides)
