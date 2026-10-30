# Manual tests (write who, when, result)

| # | Steps | Expected | Result |
|---|---|---|---|
| T1 | `make setup`, `make backend`, `make frontend`, open http://localhost:5173 | scenario list loads, idle state | |
| T2 | S2, shield off, Run scenario | attacker panel turns red, shows "Leaked: NIMBUS_API_KEY", value redacted | |
| T3 | S2, shield on, Run scenario, Show evidence on step 3 | DENIED stamps; drawer highlights line 13 with "Hidden in the original email" | |
| T4 | S5, Run, Reject / then again Approve | rejected: no payment; approved: "Paid Rs 49,000 to ACCT-11223344" | |
| T5 | S5, Run, wait 2 minutes | card shows "You didn't answer", no payment | |
| T6 | Scoreboard → Run evaluation | 9/9 → 0/9, 7/7 → 7/7, 0 | |
| T7 | Audit → Verify; run `make tamper`; Verify | intact → "Chain broken at row #N" | |
| T8 | Stop the backend, reload the UI | readable "Can't reach the backend" banner | |
| T9 | Projector 1280×720 from the back of the room | stamps and chips readable | |
| T10 | Deployed URLs (DEPLOY.md) with demo code | runs S2 off/on | |
