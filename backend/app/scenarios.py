"""Scenario files (app/scenarios/*.yaml): the user request, the world, the scripted agent plan,
what counts as the attack landing / the legit task being done, and the expected verdicts."""

from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path
from typing import Any, Literal

import yaml
from pydantic import BaseModel, Field, model_validator

SCENARIO_DIR = Path(__file__).resolve().parent / "scenarios"
FIXTURES_DIR = Path(__file__).resolve().parent / "fixtures"  # recorded live runs (app/agent/recorder.py)


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
    script: list[dict[str, Any]] = []
    # a recorded live run instead of an inline script; only a plain file name under app/fixtures/
    script_file: str | None = Field(default=None, pattern=r"^fixtures/[A-Za-z0-9_.-]+\.json$")

    @model_validator(mode="after")
    def _one_script(self) -> Scenario:
        if bool(self.script) == bool(self.script_file):
            raise ValueError("a scenario needs exactly one of script or script_file")
        if self.script_file:
            doc = json.loads((FIXTURES_DIR / Path(self.script_file).name).read_text(encoding="utf-8"))
            self.script = doc["script"]
        return self

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
