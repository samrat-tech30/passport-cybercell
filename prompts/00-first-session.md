Read CLAUDE.md, docs/PLAN.md and docs/PROGRESS.md. Then help me set up this laptop:

1. Check versions: python3 (need 3.11+), node (need 22.12+ or 20.19+), npm, git. Tell me what to install if anything is missing.
2. Run `make setup` (on Windows without make, use the commands in README.md "Without make").
3. Start the backend (`make backend`) and the frontend (`make frontend`) in two terminals, and confirm `curl -s http://localhost:8000/health` answers.
4. Run `make check` and show me the summary.
5. Tell me in 5 lines: what PASSPORT does, which file decides tool calls, what rule blocks the S2 attack, where the scenarios live, and what my first prompt file is (from docs/PLAN.md roles; ask me which member I am: M1, M2, M3 or M4).

Don't change any code in this session.
