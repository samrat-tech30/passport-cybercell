"""Request bodies. Strict limits on every field: the API is public once deployed."""

from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field


class Strict(BaseModel):
    model_config = ConfigDict(extra="forbid")


class NewSessionIn(Strict):
    scenario_id: str | None = Field(default=None, pattern=r"^[a-z0-9_]{1,32}$")
    user_request: str | None = Field(default=None, min_length=1, max_length=2000)
    shield_on: bool = True
    mode: Literal["replay", "live"] = "replay"


class ApprovalIn(Strict):
    approve: bool


class GatewaySessionIn(Strict):
    agent_name: str = Field(min_length=1, max_length=60)
    client: str = Field(min_length=1, max_length=60)
    shield_on: bool = True


class IntentIn(Strict):
    request: str = Field(min_length=1, max_length=2000)


class GatewayDecideIn(Strict):
    tool: str = Field(min_length=1, max_length=64)
    args: dict[str, Any]


class ObserveIn(Strict):
    decision_id: str = Field(min_length=1, max_length=40)
    output: str = Field(max_length=20_000)


class ContextItem(Strict):
    source: str = Field(min_length=1, max_length=200)
    trust: Literal["trusted", "untrusted", "secret"]
    text: str = Field(max_length=20_000)


class DecideIn(Strict):
    tool: str = Field(min_length=1, max_length=64)
    args: dict[str, Any]
    user_request: str = Field(min_length=1, max_length=2000)
    context: list[ContextItem] = Field(default_factory=list, max_length=50)
