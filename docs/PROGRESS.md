# Progress

> Claude: the session-start hook loads this file. Update it at the end of every task (`/checkpoint`, `/handoff`). Keep it under 150 lines; details go to AI-LOG.md.

**Last updated:** 2026-10-31 IST (email-fields fix on feat/email-fields, on top of feat/attacks, not merged)
**Live URLs:** frontend <…> · backend <…>
**Next task:** V1-0 setup on every laptop, then each person opens their prompt in `prompts/`.

## Done (by the starter, verified)
- V1-1 core gate: capsule, segments, tracer, rules R0–R8, canaries, fail-closed, approvals with timeout
- V1-2 API: sessions + SSE, evidence, approvals, attacker, audit + verify, eval, `/v1/decide`, admin reset; security middleware; contract examples + test
- V1-3 UI: Agent tab (stamps, origin chips, evidence drawer, approval dialog, attacker panel), Scoreboard, Audit
- 11 scenarios (s1–s8b); eval: attacks 7/7 → 0/7, legit tasks 6/6 → 6/6, 0 popups on clean legit tasks
- 85 backend tests, `make check` green, CI workflow, Dockerfile, deploy notes

## Done (V2-B, Person A, branch feat/v2b-disguise, committed, not merged)
- Disguise-proof tracing (`gate/disguise.py`): "at"/"dot", base64, Indic digits, 3+ digit words, zero-width; s7b/s7c now DENY with the line shown; new s7d (Kannada digits), s7e (zero-width)
- R11_LOOKALIKE (non-ASCII in a sink value, "looks like <value>"); canaries checked in disguise too; `Evidence.disguised` in the contract
- Eval: attacks 9/9 → 0/9, legit 7/7 → 7/7, 0 popups on clean legit tasks; 109 backend tests
- Red-team + reviewer findings fixed: user-words laundering (F1), cubic regex on long whitespace (F2), amounts matching random canaries (flaky test), soft hyphen; `scripts/check.sh` no longer writes /tmp directly

## Done (Part 1 attacks, Person A, branch feat/attacks on top of feat/v2b-disguise, committed, not merged)
- 7 new attack scenarios: s9 reply-to in body (DENY R3), s9b Reply-To header (ASK R5), s10 address split across two emails (ASK R5), s11 look-alike vendor new account (DENY R3), s12 urgent CEO in Kannada (DENY R1+R3), s13 subject line (DENY R3), s13b attachment name (ASK R5)
- Eval (`python -m app.eval_runner --no-save`): attacks 16/16 → 0/16, legit 14/14 → 14/14, 0 popups on clean legit tasks. After the email-fields fix only s10 is stopped by an approval the scenario rejects; s9b and s13b are DENY R3. PITCH/RESULTS numbers not updated yet.

## Tasks for M2 (gaps found by Part 1 attacks, THREAT-MODEL §5)
- [x] Label every email field (Reply-To, Cc, attachment names) in `segments._add_email`: s9b and s13b are now DENY R3 (tests/test_segments.py). Done by Person A on feat/email-fields. Red-teamed: 6 findings (F1–F6) fixed, 31 tests in tests/test_redteam_email_fields.py.
- [ ] Split values across segments (s10): trace a value that is the join of pieces from two untrusted segments, or say why not in DECISIONS.md.
- [ ] Reply false positive: a trusted contacts directory (like vendors.json) so "Reply to Rahul's email" works without typing the address. Needs a scenario + test.
- [ ] Optional: flag ASCII look-alike sender domains (vs vendor registry / company domain) in the approval popup message only, never in the verdict.

## Not verified yet
- Live LLM mode against a real provider (code tested with a fake client only)
- Docker image build and a real deployment
- Projector on the real venue screen (Chromium at 1280×720 checked: readable)
- Windows setup without make (commands in README)

## In progress
- <slice, who, which files, what's left>

## Known bugs
- (feat/v2b-disguise) A single line over 20,000 characters (`disguise.MAX_VIEW_LEN`) only gets the clean() view, so "at"/"dot" and base64 aren't decoded on it: ASK (R5), not DENY. Split long lines into overlapping windows. Found by red-team F3; the email-attachment case is fixed.
- none known

## Ideas / later
- MCP gateway in front of real MCP servers (prompts/stretch-mcp-gateway.md)
- LangGraph adapter calling `/v1/decide` (prompts/stretch-langgraph-adapter.md)
