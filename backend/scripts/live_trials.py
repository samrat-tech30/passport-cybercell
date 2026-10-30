"""Run a scenario N times against the real LLM (live mode) and report what the model did.

    cd backend
    .venv/Scripts/python scripts/live_trials.py s1 --runs 5
    .venv/Scripts/python scripts/live_trials.py s2 --runs 3 --shield off --record
    (same --base-url / --model / --key-var overrides as llm_probe.py)

Same code path as POST /sessions (create_session + run_session), in-process, nothing persisted.
Approvals are answered "reject" (the scenario's own setting is used in replay; a live run has no user).
"""

from __future__ import annotations

import argparse
import asyncio
import os
import sys

from llm_probe import load_env


async def trials(args: argparse.Namespace) -> int:
    from app.agent.loop import run_session
    from app.config import load_settings
    from app.db import database
    from app.eval_runner import score
    from app.scenarios import load_scenarios
    from app.sessions import create_session

    st = load_settings()
    if not st.live_llm_ready:
        print("live LLM not ready: set LLM_BASE_URL, LLM_MODEL and LLM_API_KEY (Ollama: any value)")
        return 2
    database.connect(st.db_path)  # read-only use: persist=False below
    sc = load_scenarios()[args.scenario]
    print(
        f"{sc.id} '{sc.title}' x{args.runs}, shield {'ON' if args.shield == 'on' else 'OFF'}, model {st.llm_model}"
    )
    for i in range(1, args.runs + 1):
        s = create_session(
            st,
            scenario=sc,
            user_request=None,
            shield_on=args.shield == "on",
            mode="live",
            approval_mode="reject",
            persist=False,
        )
        await run_session(s)
        r = score(sc, s)
        print(
            f"\n--- run {i}: status={s.status} attack_landed={r['attack_landed']} legit_done={r['legit_done']}"
        )
        for d in s.decisions.values():
            rules = ",".join(x.rule_id for x in d.reasons) or "-"
            args_s = str(s.world.redact(d.args))[:140]
            print(f"  {d.tool:<20} {d.verdict.value:<17} ran={d.executed!s:<5} {rules:<40} {args_s}")
        last = s.bus.events[-1]
        print(f"  end: {last.type}: {str(last.data.get('answer') or last.data.get('message', ''))[:200]}")
    return 0


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("scenario")
    ap.add_argument("--runs", type=int, default=3)
    ap.add_argument("--shield", choices=["on", "off"], default="off")
    ap.add_argument(
        "--record", action="store_true", help="save each run to app/fixtures/ (RECORD_FIXTURES=1)"
    )
    ap.add_argument("--base-url")
    ap.add_argument("--model")
    ap.add_argument("--key-var")
    args = ap.parse_args()
    load_env(args)
    if args.record:
        os.environ["RECORD_FIXTURES"] = "1"
    sys.exit(asyncio.run(trials(args)))


if __name__ == "__main__":
    main()
