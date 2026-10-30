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
- [ ] [auto] s7b and s7c become DENY with the line shown; Kannada/Devanagari digits and look-alike letters covered; 3 false-positive tests pass
## V2-C Herd immunity (prompts/v2-C-herd-immunity.md)
- [ ] [auto] value blocked in session A → R12 in session B; same poisoned email quarantined before B's LLM sees it
- [ ] [hand] two-window demo works
## V2-E MCP gateway (prompts/v2-E-mcp-gateway.md; replaces V2-D)
- [ ] [auto] s2 over MCP: read ALLOW, attacker send DENY with rule + line, legit send ALLOW (integrations/mcp_gateway/tests)
- [ ] [auto] fail closed: tool before `start_task`, second `start_task`, backend down, REQUIRE_APPROVAL without approval → all refused; the tool never runs
- [ ] [hand] the s2 example works in Claude Desktop or the MCP Inspector; gateway calls show in the Audit tab
## V2-D Payment visa (prompts/v2-D-payment-visa.md; dropped for V2-E, only if everything else is done)
- [ ] [auto] direct tool call without visa, edited args, reused visa, expired visa → all refused; approved flow still pays

## E-1 Demo ready (by 12:00)
- [ ] [hand] PITCH.md rehearsed 3 times under 3:00
- [ ] [hand] Backup video recorded (2 min) and on the laptop desktop
- [ ] [auto] `make check` green on `main`; RESULTS.md matches `make eval`
- [ ] [hand] Submitted by 14:30 (repo, video, slides)
