# Glossary (use the same words in UI, code, pitch)

| Word | Meaning |
|---|---|
| Gate / PASSPORT | the layer that decides every tool call (code: `app/gate/`) |
| Passport (of a value) | where an argument value was born: user, trusted, secret, untrusted, model-invented |
| Sink argument | an argument that steers where an action goes or what it touches (recipient, path, account, amount, secret key) |
| Soft sink | a sink that may legitimately come from a document (invoice amount): ask instead of deny |
| Segment | one labelled piece of text the session has seen (an email, a file, the user's request) |
| Intent capsule / frozen intent | what the user asked for, extracted from their words before reading anything |
| Canary | a fake secret with a random value; seeing it in an argument proves exfiltration |
| Shield on / off | gate enforces / gate only logs (demo "before" mode) |
| Verdict | ALLOW, REQUIRE_APPROVAL ("Needs you"), DENY |
| Fail closed | any error or missing answer = DENY |
| Confused deputy | an agent with real permissions tricked into using them for an attacker |
| Replay mode | the agent's tool-call plan is recorded; the gate decides live |
| Trifecta | secret seen + untrusted content seen + data leaving (R8) |
