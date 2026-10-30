"""Request bodies. Strict limits on every field: the API is public once deployed."""

from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator


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


class CatalogTool(Strict):
    """Everything the agent is shown about a tool: all of it is attacker-writable."""

    name: str = Field(min_length=1, max_length=64)
    description: str = Field(default="", max_length=4000)
    input_schema: dict[str, Any] = Field(default_factory=dict)
    title: str | None = Field(default=None, max_length=200)
    annotations: dict[str, Any] | None = None
    output_schema: dict[str, Any] | None = None


class CatalogIn(Strict):
    server: str = Field(min_length=1, max_length=60)
    tools: list[CatalogTool] = Field(max_length=50)

    @model_validator(mode="after")
    def _unique_names(self) -> CatalogIn:
        names = [t.name for t in self.tools]
        if len(names) != len(set(names)):
            raise ValueError("tool names must be unique")  # a second definition would be silently dropped
        return self


class ContextItem(Strict):
    source: str = Field(min_length=1, max_length=200)
    trust: Literal["trusted", "untrusted", "secret"]
    text: str = Field(max_length=20_000)


class DecideIn(Strict):
    tool: str = Field(min_length=1, max_length=64)
    args: dict[str, Any]
    user_request: str = Field(min_length=1, max_length=2000)
    context: list[ContextItem] = Field(default_factory=list, max_length=50)
