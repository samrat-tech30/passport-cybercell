# Decisions

One line each: `date — decision — why — what we gave up`. Never delete a line; add a new one if a decision changes.

- 2026-10-30 — Track: AgentShield (AI-agent security) — best before/after demo, newest threat, team built an agent at the TCS hackathon — gave up the TrustLens India-scam story (reused in v2-A)
- 2026-10-30 — Core idea: per-argument provenance ("passport") checked deterministically before every tool call — survives rewording/translation; LLM classifiers can be injected — gave up semantic understanding of text
- 2026-10-30 — No LangChain/LangGraph in the core; plain Python agent loop — the gate is the product, frameworks add learning time and version risk tonight — answer "does it integrate?" with `POST /v1/decide` (+ MCP gateway as stretch)
- 2026-10-30 — Backend FastAPI + Pydantic v2; DB SQLite with SQL migrations — zero setup, one file, enough for a demo — no multi-instance scaling
- 2026-10-30 — Frontend React + Vite + TypeScript, plain CSS tokens, no UI kit/Tailwind/router — fewer moving parts, full control of the look — more CSS by hand
- 2026-10-30 — Frontend and backend deployed separately from one repo; frontend calls backend directly with a CORS allowlist — matches "deploy at different servers" — must set ALLOWED_ORIGINS and VITE_API_URL correctly
- 2026-10-30 — Live updates via Server-Sent Events, not WebSockets — one direction is all we need, works through proxies, auto-reconnect — no client→server messages over the stream (approvals use POST)
- 2026-10-30 — Replay mode (scripted plan per scenario) as the default demo mode — no Wi-Fi/LLM dependence, reproducible eval; the gate still runs live — must say openly that the agent plan is recorded
- 2026-10-30 — Naive assistant persona that follows instructions found in documents — makes the shield-OFF attack reproducible; realistic for many assistants — the live model may still refuse sometimes
- 2026-10-30 — Intent capsule built by regex + keyword patterns, no LLM — can't be injected — misses unusual phrasings (falls back to R6 approval)
- 2026-10-30 — Invoice amount is a "soft sink" (untrusted → ask, not deny) — real invoices state the amount — the user must check the amount
- 2026-10-30 — Naming an email address in the request unlocks send_email; the word "email" alone only unlocks reading — "summarise my emails" must not let the agent send
- 2026-10-30 — Canary secrets random per session and redacted everywhere — a fixed fake key could still be logged/committed — none
- 2026-10-30 — Audit log: SHA-256 hash chain in SQLite, no blockchain — tamper-evident, simple — truncation of the tail not detected by the chain alone
- 2026-10-30 — Added R8_TRIFECTA (secret + untrusted + egress → ask); v2 rules renumbered R9–R12 (the earlier build-spec doc said R8–R11) — covers paraphrased secrets — one more approval in that rare case
- 2026-10-30 — V2-B disguise-proof tracing: clean "views" of each line (NFKC, zero-width stripped, Indic digits, 3+ digit-word runs, spoken at/dot/dash/underscore, one level of base64), deterministic, no LLM — the LLM writes the clean value, so exact matching alone sent s7b/s7c to R5 — more string work per decision (cached per line)
- 2026-10-30 — The disguise pass searches ALL four origins (user → trusted → secret → untrusted), not only untrusted + secret as the V2-B prompt said, and each origin finishes its exact AND disguise pass before the next one — keeps invariant 6 (the user wins ties: "priya at nimbus dot test" typed by the user beats an email that has priya@nimbus.test) — a value can now be USER through a disguised view of the user's own words
- 2026-10-30 — Disguise matches need 6+ characters, and amounts only match whole numbers in spaced views — stops squashed text from inventing matches ("14 99" → 1499, 200 inside 12000) — very short disguised values still go to R5
- 2026-10-30 — Canaries also checked in clean views; when a secret is only visible in a view (zero-width split, inside a longer base64), redact() hides the whole value — a disguised secret can't be cut out cleanly — that one value shows as "[secret:NAME in disguise]"
- 2026-10-30 — R11_LOOKALIKE (DENY, risk 90): any non-ASCII character in a string sink value; look-alike folding (Cyrillic/Greek map) is used only for the "looks like <value>" message, never to accept — folding before an allowlist check is exactly the attack — internationalised addresses would be denied
