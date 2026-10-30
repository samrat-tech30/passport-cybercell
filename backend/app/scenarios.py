"""Scenario files (app/scenarios/*.yaml): the user request, the world, the scripted agent plan,
what counts as the attack landing / the legit task being done, and the expected verdicts."""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from typing import Any, Literal

import yaml
from pydantic import BaseModel, Field

SCENARIO_DIR = Path(__file__).resolve().parent / "scenarios"


class WorldSpec(BaseModel):
    inbox: str = "base"
    file_overrides: dict[str, str] = {}


class Expectation(BaseModel):
    tool: str
    args: dict[str, Any] = {}  # subset that must match
    verdict: Literal["ALLOW", "REQUIRE_APPROVAL", "DENY"]
    rules: list[str] = []  # each must be among the reasons that fired


class Scenario(BaseModel):
    id: str = Field(pattern=r"^[a-z0-9_]{1,32}$")
    title: str
    category: Literal[
        "legitimate",
        "injected_document",
        "sensitive_data",
        "beyond_permission",
        "high_impact",
        "disguised",
        "fail_closed",
    ]
    user_request: str
    world: WorldSpec = WorldSpec()
    approvals: Literal["approve", "reject", "timeout"] = "reject"
    fault: Literal["gate_error"] | None = None
    attack_success_if: list[str] = []
    legit_done_if: list[str] = []
    expect_on: list[Expectation] = []
    v2_note: str | None = None
    script: list[dict[str, Any]]

    @property
    def is_attack(self) -> bool:
        return bool(self.attack_success_if)


@lru_cache(maxsize=1)
def load_scenarios() -> dict[str, Scenario]:
    out: dict[str, Scenario] = {}
    for f in sorted(SCENARIO_DIR.glob("*.yaml")):
        sc = Scenario.model_validate(yaml.safe_load(f.read_text(encoding="utf-8")))
        if sc.id in out:
            raise ValueError(f"duplicate scenario id {sc.id}")
        out[sc.id] = sc
    return out
