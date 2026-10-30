---
name: passport-gate
description: How the PASSPORT security gate works and how to change it safely - the invariants, the rules R0-R8, the tracer, the segment store, the intent capsule, tools, the fake world and scenarios. Use for ANY change in backend/app/gate/, backend/app/tools/, backend/app/world_data/, backend/app/scenarios/, policy.yaml or eval_runner.py, and when adding a rule, a tool, an attack scenario or a v2 upgrade.
---

# The PASSPORT gate

One sentence: **before any tool runs, every sink argument must show where it was born; values born in untrusted content can't steer actions, and secrets can't leave.**

## The flow (backend/app/gate/handle.py)
`decide()` → if REQUIRE_APPROVAL: ask the user (timeout = no) → execute the tool → `store.ingest()` labels the output → save decision + audit row + stream events → return text to the agent.
Shield OFF: same decision is computed and logged, but the tool runs anyway. That's how the "before" half of the demo works. Never remove that logging.

## Invariants (break one = the project is broken)
1. Only `handle.py` calls `run_tool()`. Tools return confirmations without echoing input values ("Email sent."), or the echoed value would get a passport it didn't earn.
2. `decide()` never raises and never returns ALLOW on error: everything is wrapped and turns into R0_FAIL_CLOSED.
3. `decide()` is deterministic: no LLM, no network, no clock or randomness in the verdict.
4. The intent capsule is built from the user's text only, before any tool runs.
5. Secrets (vault canaries) are preloaded as hidden SECRET segments so they can never be laundered through untrusted text, and every value shown/stored/streamed goes through `world.redact()`.
6. Tracing order is user → trusted → secret → untrusted. The user wins ties; secrets beat untrusted.
7. Only our own config is TRUSTED (vendor registry). Everything a tool reads from the outside world is UNTRUSTED.

## The rules (policy.yaml has the risk numbers)
| Rule | Fires when | Verdict |
|---|---|---|
| R0_FAIL_CLOSED | gate error, unknown tool, invalid args, approval timeout | DENY |
| R1_PROFILE | tool not in the assistant's profile | DENY |
| R2_CANARY | a vault secret in any argument (raw, base64, hex, URL-encoded, reversed) | DENY |
| R3_SINK_UNTRUSTED | a sink argument was born in untrusted content | DENY |
| R4_SECRET_EGRESS | a secret value in an egress tool argument | DENY |
| R5_SINK_INVENTED | sink value found nowhere, after untrusted content was read | REQUIRE_APPROVAL |
| R6_OUT_OF_INTENT | tool not in the capsule, or amount over the user's limit | REQUIRE_APPROVAL |
| R7_HIGH_IMPACT | high-impact tool, or a soft sink (invoice amount) from a document | REQUIRE_APPROVAL |
| R8_TRIFECTA | session saw a secret AND untrusted content, and the call is egress | REQUIRE_APPROVAL |
Final verdict = strongest reason (DENY > ASK > ALLOW). Primary rule = highest-risk reason with that verdict. All reasons are kept as evidence.
v2 adds R9_MANDATE_PAYEE, R10_MANDATE_AMOUNT, R11_LOOKALIKE, R12_KNOWN_THREAT (see prompts/v2-*.md). Adding a rule = add it to `RULE_IDS` in policy.py AND `risk:` in policy.yaml, or start-up fails.

## How to add things
- **A rule:** policy.yaml (`risk`), policy.py (`RULE_IDS`), decide.py (one `add(...)` call with a plain-English message that names the source and line), a unit test in `tests/test_decide.py`, a scenario if it's demo-worthy, a line in DECISIONS.md, `make eval`.
- **A tool:** `tools/world.py` (in-memory effect, `ToolError` for bad input, no real I/O, no echoing values), `tools/registry.py` (`ToolSpec` with params and `output_trust`), `segments.py` `ingest()` if its output carries text, `policy.yaml` (profile, sinks, egress, high_impact), tests.
- **A scenario:** YAML in `app/scenarios/` (quote titles!), synthetic content in `world_data/`, a scripted plan of what a fooled agent would do (`{{secret:NAME}}` only resolves if the agent really read it), `attack_success_if`, `legit_done_if`, `expect_on`. `tests/test_scenarios.py` picks it up automatically and checks: attack lands OFF, fails ON, legit part still works ON.
- **Conditions** for scenarios: `attacker_received`, `email_sent_to:<addr>`, `paid:<account>`, `file_deleted:<path>`, `secret_read:<key>`.

## Honest limits (say them, don't hide them)
- Exact matching misses disguised values ("x at evil dot test", base64): v1 falls back to R5 (ask), never ALLOW. v2 upgrade B fixes this.
- PASSPORT reasons about where values came from, not what text means: a biased summary with no tool effect isn't stopped.
- A user who types the attacker's details themselves is trusted (they're the user).
- Replay mode replays a recorded plan; the gate still runs live. Say this to judges.

## Before you say done
`make check` green, `make eval` shows 0 attacks landed with shield ON and no drop in legit tasks, red-teamer run on gate changes.
