"""Every scenario, shield OFF and ON. This is criterion 02: the attack works before, fails after."""

import asyncio

import pytest

from app.contracts import Verdict
from app.eval_runner import run_scenario
from app.scenarios import load_scenarios

SCENARIOS = list(load_scenarios().values())


def matches(decision, exp):
    return decision.tool == exp.tool and all(str(decision.args.get(k)) == str(v) for k, v in exp.args.items())


@pytest.mark.parametrize("sc", SCENARIOS, ids=[s.id for s in SCENARIOS])
def test_shield_on_gives_expected_verdicts(sc):
    s = asyncio.run(run_scenario(sc, shield_on=True))
    decisions = list(s.decisions.values())
    for exp in sc.expect_on:
        found = [d for d in decisions if matches(d, exp)]
        assert found, f"no decision for {exp.tool} {exp.args}"
        d = found[0]
        assert d.verdict == Verdict(exp.verdict), f"{exp.tool}: {d.verdict} ({d.message})"
        assert set(exp.rules) <= {r.rule_id for r in d.reasons}, (
            f"{exp.tool}: rules {[r.rule_id for r in d.reasons]}"
        )


@pytest.mark.parametrize("sc", [s for s in SCENARIOS if s.is_attack], ids=lambda s: s.id)
def test_attack_lands_with_shield_off_and_fails_with_shield_on(sc):
    off = asyncio.run(run_scenario(sc, shield_on=False))
    on = asyncio.run(run_scenario(sc, shield_on=True))
    assert any(off.world.happened(c) for c in sc.attack_success_if), "the attack must work without PASSPORT"
    assert not any(on.world.happened(c) for c in sc.attack_success_if), "the attack must fail with PASSPORT"


@pytest.mark.parametrize(
    "sc", [s for s in SCENARIOS if s.legit_done_if and s.category != "fail_closed"], ids=lambda s: s.id
)
def test_legit_part_of_the_task_still_works_with_shield_on(sc):
    on = asyncio.run(run_scenario(sc, shield_on=True))
    assert all(on.world.happened(c) for c in sc.legit_done_if)


def test_secrets_never_reach_the_database_or_audit_log():
    sc = load_scenarios()["s2"]
    s = asyncio.run(run_scenario(sc, shield_on=False))
    from app.db.database import query

    dump = " ".join(
        str(tuple(r)) for t in ("decisions", "world_events", "audit_log") for r in query(f"SELECT * FROM {t}")
    )
    for value in s.world.vault.values():
        assert value not in dump
