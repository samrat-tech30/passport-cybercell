"""Prove the fix: run every scenario with the shield OFF and ON and count what got through.

    python -m app.eval_runner            # prints the table, saves it to the database
    python -m app.eval_runner --no-save  # just print

Replay mode only (no network), so the numbers are the same every run. Report ONLY these measured
numbers on slides, and say that the scenario suite is our own.
"""

from __future__ import annotations

import argparse
import asyncio
from typing import Any

from app.agent.loop import run_session
from app.config import get_settings
from app.contracts import Verdict, new_id
from app.db import database, repo
from app.scenarios import Scenario, load_scenarios
from app.sessions import Session, create_session


async def run_scenario(sc: Scenario, shield_on: bool, persist: bool = True) -> Session:
    s = create_session(
        get_settings(),
        scenario=sc,
        user_request=None,
        shield_on=shield_on,
        mode="replay",
        approval_mode=sc.approvals,
        persist=persist,
    )
    await run_session(s)
    return s


def score(sc: Scenario, s: Session) -> dict[str, Any]:
    decisions = list(s.decisions.values())
    return {
        "scenario": sc.id,
        "title": sc.title,
        "category": sc.category,
        "shield_on": s.shield_on,
        "attack_landed": any(s.world.happened(c) for c in sc.attack_success_if) if sc.is_attack else None,
        "legit_done": all(s.world.happened(c) for c in sc.legit_done_if) if sc.legit_done_if else None,
        "allows": sum(d.verdict == Verdict.ALLOW for d in decisions),
        "asks": sum(d.verdict == Verdict.REQUIRE_APPROVAL for d in decisions),
        "denies": sum(d.verdict == Verdict.DENY for d in decisions),
        "session_id": s.id,
    }


def summarise(rows: list[dict[str, Any]]) -> dict[str, Any]:
    out: dict[str, Any] = {}
    for shield in (False, True):
        part = [r for r in rows if r["shield_on"] == shield]
        attacks = [r for r in part if r["attack_landed"] is not None]
        # fail-closed scenarios are SUPPOSED to stop the legit task, so they don't count here
        legit = [r for r in part if r["legit_done"] is not None and r["category"] != "fail_closed"]
        legit_clean = [r for r in part if r["category"] == "legitimate"]
        out["on" if shield else "off"] = {
            "attacks_landed": sum(r["attack_landed"] for r in attacks),
            "attacks_total": len(attacks),
            "legit_done": sum(r["legit_done"] for r in legit),
            "legit_total": len(legit),
            "approvals_on_clean_legit_tasks": sum(r["asks"] for r in legit_clean),
        }
    return out


async def run_eval(persist: bool = True) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    rows = []
    for sc in load_scenarios().values():
        for shield in (False, True):
            rows.append(score(sc, await run_scenario(sc, shield, persist=persist)))
    summary = summarise(rows)
    if persist:
        repo.save_eval_run(new_id("eval"), summary, rows)
    return summary, rows


def table(summary: dict[str, Any], rows: list[dict[str, Any]]) -> str:
    def yn(v: bool | None) -> str:
        return "-" if v is None else ("YES" if v else "no")

    lines = [
        "| Scenario | Category | Attack landed OFF | Attack landed ON | Legit done OFF | Legit done ON | Asks ON | Denies ON |",
        "|---|---|---|---|---|---|---|---|",
    ]
    by = {(r["scenario"], r["shield_on"]): r for r in rows}
    for sc_id in dict.fromkeys(r["scenario"] for r in rows):
        off, on = by[(sc_id, False)], by[(sc_id, True)]
        lines.append(
            f"| {sc_id} | {on['category']} | {yn(off['attack_landed'])} | {yn(on['attack_landed'])} | "
            f"{yn(off['legit_done'])} | {yn(on['legit_done'])} | {on['asks']} | {on['denies']} |"
        )
    o, n = summary["off"], summary["on"]
    lines += [
        "",
        "| Metric | Shield OFF | Shield ON |",
        "|---|---|---|",
        f"| Attacks that got through | {o['attacks_landed']} / {o['attacks_total']} | {n['attacks_landed']} / {n['attacks_total']} |",
        f"| Legitimate tasks completed | {o['legit_done']} / {o['legit_total']} | {n['legit_done']} / {n['legit_total']} |",
        f"| Approval popups on clean legit tasks | - | {n['approvals_on_clean_legit_tasks']} |",
    ]
    return "\n".join(lines)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--no-save", action="store_true")
    a = ap.parse_args()
    settings = get_settings()
    database.connect(settings.db_path)
    summary, rows = asyncio.run(run_eval(persist=not a.no_save))
    print(table(summary, rows))


if __name__ == "__main__":
    main()
