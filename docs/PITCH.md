# Pitch: 3 minutes + Q&A

Numbers only from RESULTS.md. Facts only from FACTS.md. Replay mode on stage (say it).

| Time | Who | Screen | Say |
|---|---|---|---|
| 0:00–0:20 | M4 | Title slide | "An email made Microsoft 365 Copilot leak data with zero clicks (EchoLeak). The agent had every permission it needed. The attacker didn't hack the agent: they borrowed it. That's indirect prompt injection, OWASP's number one LLM risk." |
| 0:20–0:35 | M4 | Threat-model slide | "Our attacker can't talk to the agent. They can only write text it reads: an email, an invoice, a document." |
| 0:35–1:00 | M3 | Agent tab, S2, **shield off**, Run | "The user asks for an inbox summary to Priya. Email #3 hides one white line. Watch the right panel." → attacker panel shows the leaked API key (redacted canary). |
| 1:00–1:45 | M3 | Same S2, **shield on**, Run → Show evidence | "Same email, same agent. Every argument must show a passport. Priya came from your words: allowed. audit-team@evil.test exists only in Email #3, line 13: denied. Here's the hidden line. Rewording or translating it changes nothing: the address still wasn't born in your words." |
| 1:45–2:05 | M3 | S5 approval popup → Reject/Approve | "Payments always ask, and show only the risky value and where it came from. No answer in two minutes means no." |
| 2:05–2:25 | M2 | Scoreboard tab → Run evaluation | "Every scenario, shield off and on: attacks that got through 7 of 7 → 0 of 7, legitimate tasks 6 of 6 kept, zero popups on clean tasks. Measured, and our test suite is in the repo." (+ v2 result if built) |
| 2:25–2:45 | M1 | Audit tab, `make tamper` in a terminal, Verify | "Every decision is in a hash chain. Change one row and verification breaks at that row." |
| 2:45–3:00 | M4 | Closing slide | "Don't secure the prompt. Check the passport of every argument. Any framework can call `/v1/decide` before running a tool." |

## What's new (say it honestly)
"Checking where data came from is known research: CaMeL, FIDES, PACT. We credit them. Ours decides **per argument**, so the legit part of the task keeps working; it **shows the user the exact line** a bad value came from; it runs as a **drop-in API**; and [v2 pieces built: UPI mandate lock for agentic payments in India · disguise-proof tracing in Hindi/Kannada/base64 · herd immunity across agents · argument-bound payment visas]."

## Judge Q&A
| Question | Answer | Who |
|---|---|---|
| Why not a guard LLM? | It can be injected too. Our decision is deterministic code over where values came from; the LLM is allowed to be fooled, it just can't act on it. | M2 |
| Isn't this CaMeL / FIDES? | Same principle, credited. They block whole flows once untrusted data is in scope; we decide per argument, show evidence lines, and drop in over HTTP. | M2 |
| What if the attacker rewords or translates? | The verdict never reads the wording: the address still exists only in the email (s7a Hindi is denied). Disguised addresses ("at"/"dot", base64, Kannada digits, invisible characters) are traced back and denied too (s7b–s7e); disguises we don't decode go to approval, never allowed. | M2 |
| Isn't the agent scripted? | In replay mode the agent's plan is recorded so the demo is reproducible; every gate decision is computed live. Live LLM mode uses <provider/model>. | M1 |
| False positives? | 0 popups on clean legit tasks, 6/6 legit tasks completed with the shield on (RESULTS.md). | M2 |
| What if the user types the attacker's address? | Then it's the user's intent; out of scope, and in our threat model. | M4 |
| Where's LangChain? | We didn't need it: the gate is framework-agnostic. Any LangChain/LangGraph/CrewAI agent calls `POST /v1/decide` before a tool. | M1 |
| Is the data real? | No: synthetic company, `.test` domains, random canary keys, tools act in memory only. | M4 |
| How is your own app secured? | docs/SECURITY.md: strict validation, security headers, CORS allowlist, rate limits, access code, secrets redacted everywhere, audit hash chain. | M1 |
| What did AI do? | Claude Code wrote code under our direction; every slice was reviewed and tested (docs/AI-LOG.md). We can explain every part. | all |
