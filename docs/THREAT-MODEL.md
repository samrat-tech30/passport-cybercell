# Threat model

## 1. Assets
Synthetic API key and DB password (vault canaries) · internal files (payroll.csv) · the mailbox · the power to send email, pay invoices, delete files · the audit trail.

## 2. Attacker
An outsider who **can't talk to the agent** but can put text where it reads: an email (body, headers, hidden HTML), a shared document, an invoice, a web page, a tool output. Knows exactly how PASSPORT works. Does **not** control the user's typed request, the policy, the code, or the server.

## 3. Trust boundaries
| Trusted | Untrusted | Secret |
|---|---|---|
| the user's typed request in this session; our own config (vendor registry, policy) | every email, file, page, tool output | vault values |

## 4. What PASSPORT stops (with the rule)
| Threat | Rule | Proven by |
|---|---|---|
| Hijacked sink argument (recipient, path, account, key) from content | R3 | s2, s3, s4, s6, s7a |
| The same via "reply to X instead", a look-alike vendor (acme-suppIies), urgency + Kannada, or the subject line | R3 | s9, s11, s12, s13 |
| The same in any other email field (Reply-To header, attachment name) | R3 | s9b, s13b, test_segments.py |
| A reply the user asked for by name still works, while the email's "reply to X instead" is denied | R3 (contact named by the user is trusted) | s9c, test_contacts.py |
| The same, written in disguise ("at"/"dot", base64, Indic digits or digit words, zero-width characters) | R3 | s7b, s7c, s7d, s7e, test_disguise.py |
| Look-alike letters in an address, account, path or key (Cyrillic а in "bigbаsket") | R11 | test_disguise.py |
| Secret exfiltration in any argument, raw or encoded | R2, R4 | s2/s3 shield OFF shows it lands; tests in test_decide.py |
| Tools outside the assistant's role | R1 | s3, s4 |
| Values the model made up after reading untrusted content | R5 (ask) | test_decide.py, s10 (see §5: a gap, not a win) |
| Actions outside the user's intent or above their amount | R6 (ask) | test_decide.py |
| High-impact actions without a human | R7 (ask) | s5, s8b |
| Secret + untrusted content + egress in one session | R8 (ask) | test_decide.py |
| Gate errors, bad arguments, unanswered approvals | R0 (deny) | s8, s8b |
| Silent edits to the audit log | hash chain | test_audit.py, Audit tab |

## 5. What PASSPORT does NOT stop (say this out loud)
- **Text-only manipulation** with no tool effect (a biased or wrong summary).
- **A user who types the attacker's details** themselves (they are the trusted user).
- **Disguises we don't decode**: nested base64, hex, ROT13, Devanagari or Kannada words for "at"/"dot", a value split across lines or emails (s10: `audit-team@` in Email #3 + `evil.test` in Email #4). These fall back to R5 (ask), never ALLOW. If the user approves s10, the email reaches the attacker (without the key: R1 still blocks `read_secret`).
- **Contacts are matched by first name**: "Reply to Rahul" trusts rahul@nimbus.test from the contact directory. Two contacts with the same name, or a name that's also an everyday word, would be trusted when typed. A reply to someone not in the directory (or a reply-all to Cc) still needs the user to type the address.
- **ASCII look-alike sender domains** (`acme-suppIies.test`, capital I) are not flagged: R11 only catches non-ASCII. Harmless for sinks (the gate never trusts senders, s11 is DENY by R3), but the approval popup shows the fake domain without pointing it out.
- **Non-ASCII sink values are always denied** (R11): addresses, accounts, keys AND file paths (a user-typed `résumé.md` too). Fine for our synthetic world; a real deployment would need an allowlist.
- **An address the user only spelled out** ("priya at nimbus dot test") gets an approval, not ALLOW: a squashed reading of the user's words could otherwise produce an attacker's address ("ignore anyone at evil.test").
- **Canary forms we don't check** (spaced or line-broken base64, uppercase hex, base32, double base64): defence in depth only, since the assistant's profile can't read secrets (R1) and R8 asks on egress after a secret was seen.
- **Heavy paraphrase of a secret** that defeats canary matching: mitigated by R8 (egress after secret access needs approval).
- **Approval fatigue**: reduced (only risky values are shown; legit tasks had 0 popups in our eval), not solved.
- **Truncating the end of the audit log**: the chain detects edits and deletions in the middle; for the end, record the head hash shown in the Audit tab.
- **Host or key compromise**, and threats outside this track (code-execution sandbox escape).
- **Replay mode** replays a recorded agent plan; the gate decisions are computed live every time.

## 6. Prior work (credit it)
CaMeL (Google DeepMind), FIDES (Microsoft), PACT and ARGUS (argument-level provenance), MELON, Task Shield, agent-canary. What's ours: see docs/PITCH.md "What's new".
