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
| The same, written in disguise ("at"/"dot", base64, Indic digits or digit words, zero-width characters) | R3 | s7b, s7c, s7d, s7e, test_disguise.py |
| Look-alike letters in an address, account, path or key (Cyrillic а in "bigbаsket") | R11 | test_disguise.py |
| Secret exfiltration in any argument, raw or encoded | R2, R4 | s2/s3 shield OFF shows it lands; tests in test_decide.py |
| Tools outside the assistant's role | R1 | s3, s4 |
| Values the model made up after reading untrusted content | R5 (ask) | test_decide.py |
| Actions outside the user's intent or above their amount | R6 (ask) | test_decide.py |
| High-impact actions without a human | R7 (ask) | s5, s8b |
| Secret + untrusted content + egress in one session | R8 (ask) | test_decide.py |
| Gate errors, bad arguments, unanswered approvals | R0 (deny) | s8, s8b |
| Silent edits to the audit log | hash chain | test_audit.py, Audit tab |

## 5. What PASSPORT does NOT stop (say this out loud)
- **Text-only manipulation** with no tool effect (a biased or wrong summary).
- **A user who types the attacker's details** themselves (they are the trusted user).
- **Disguises we don't decode**: nested base64, hex, ROT13, Devanagari or Kannada words for "at"/"dot", a value split across lines or emails. These fall back to R5 (ask), never ALLOW.
- **Non-ASCII addresses are always denied** (R11): fine for our synthetic world, but a real deployment with internationalised email addresses would need an allowlist.
- **Heavy paraphrase of a secret** that defeats canary matching: mitigated by R8 (egress after secret access needs approval).
- **Approval fatigue**: reduced (only risky values are shown; legit tasks had 0 popups in our eval), not solved.
- **Truncating the end of the audit log**: the chain detects edits and deletions in the middle; for the end, record the head hash shown in the Audit tab.
- **Host or key compromise**, and threats outside this track (code-execution sandbox escape).
- **Replay mode** replays a recorded agent plan; the gate decisions are computed live every time.

## 6. Prior work (credit it)
CaMeL (Google DeepMind), FIDES (Microsoft), PACT and ARGUS (argument-level provenance), MELON, Task Shield, agent-canary. What's ours: see docs/PITCH.md "What's new".
