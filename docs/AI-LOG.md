# AI log

Hackathons ask how AI was used. One row per finished step.

| Date | Slice | What Claude did | What the human did (decided, reviewed, tested) |
|---|---|---|---|
| 2026-10-30 | starter | Built the v1 core (gate, tools, DB, API, security, UI), 85 tests, docs, prompts, from the team build spec | Chose the track and approach, wrote the research pack and build spec, reviewed the starter |
| 2026-10-30 | V1-4 | Probe + trials scripts, fixture recorder and `script_file:`, timeout/429 handling, UI live toggle, 14 tests; ran Ollama llama3.2 and Groq gpt-oss-120b live and reported results; tested a stronger persona | Created the Groq key, chose the stronger persona, set the 23:30 replay rule |
| 2026-10-31 | G0 | Wrote the Gateway API contract, ARCHITECTURE §8, THREAT-MODEL gateway limits, 3 DECISIONS, ACCEPTANCE G1–G5, .env.example vars; verified the MCP SDK's 60 s default timeout; flagged 3 spec conflicts (GET token, demo code / rate limit, wait vs APPROVAL_TIMEOUT_S) and aligned the rate limit with G1 | |
