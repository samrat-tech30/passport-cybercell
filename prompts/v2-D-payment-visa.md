Slice V2-D: argument-bound payment visas. ONLY if everything else is green at 08:00. Use verify-before-use for PyJWT (EdDSA support needs `pyjwt[crypto]`; check the installed version's docs). Plan first, wait for my OK.

## Why
The gate only protects calls that go through it. A bug, a second script, or an edited request could call a payment tool directly, or change the payee after approval. European payment rules (PSD2 "dynamic linking") tie an approval to the exact amount and payee; we do the same for agents.

## Build
1. `backend/app/gate/visa.py`: Ed25519 key pair generated at start-up (or loaded from `VISA_PRIVATE_KEY_PEM` env; add to config.py + .env.example; never log it). `issue(tool, args, decision_id)` → JWT (alg EdDSA) with claims `tool`, `args_sha256` (SHA-256 of canonical JSON of the args), `decision`, `jti` (random), `iat`, `exp` = iat + 30 s. `check(token, tool, args)` verifies signature, expiry, tool, args hash, and single use (store used jti in memory + SQLite).
2. `handle.py`: when a payment tool (pay_invoice, upi_pay) is allowed or approved, issue a visa and pass it to the tool. The tool functions call `visa.check()` FIRST and raise ToolError without a valid visa. Shield OFF: issue anyway (so the "before" demo still lands) but log `visa_issued_shield_off`.
3. Audit events: `visa_issued`, `visa_rejected` (with reason, no token).
4. Demo script `backend/scripts/visa_demo.py`: (a) call the payment tool directly with no visa → rejected; (b) get a valid visa for ₹180, change the amount to 1,499 → rejected (hash mismatch); (c) reuse a visa → rejected; (d) wait 31 s → expired. Print one line per case.
5. Tests for all four cases + the normal approved flow still pays.
6. UI: a small "visa" badge with the short jti on allowed payment cards.

Docs: SECURITY.md, ARCHITECTURE.md, DECISIONS.md, PITCH.md Q&A ("What if someone calls the tool directly?"). Acceptance: V2-D lines. `make check` green.
