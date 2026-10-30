"""Shared data shapes. Everyone codes against these.

Change order (see .claude/skills/api-contracts): contracts/README.md first, then this file,
then frontend/src/lib/api/types.ts, then tests. JSON field names are snake_case.
"""

from __future__ import annotations

import time
import uuid
from enum import StrEnum
from typing import Any, Literal

from pydantic import BaseModel, Field


def new_id(prefix: str) -> str:
    return f"{prefix}_{uuid.uuid4().hex[:10]}"


class Trust(StrEnum):
    """Label on a piece of text the agent (or the gate) has seen."""

    USER = "user"  # typed by the user in this session
    TRUSTED = "trusted"  # our own config, e.g. the vendor registry
    UNTRUSTED = "untrusted"  # emails, files, web pages, tool outputs
    SECRET = "secret"  # noqa: S105 - a label name, not a password. Vault values (canaries in this demo)


class Origin(StrEnum):
    """Where one argument value was born (result of tracing)."""

    USER = "user"
    TRUSTED = "trusted"
    UNTRUSTED = "untrusted"
    SECRET = "secret"  # noqa: S105 - a label name, not a password
    MODEL_INVENTED = "model_invented"  # found nowhere: the model wrote it itself
    CONSTANT = "constant"  # too short to trace meaningfully


class Verdict(StrEnum):
    ALLOW = "ALLOW"
    REQUIRE_APPROVAL = "REQUIRE_APPROVAL"
    DENY = "DENY"


VERDICT_RANK = {Verdict.ALLOW: 0, Verdict.REQUIRE_APPROVAL: 1, Verdict.DENY: 2}


class Segment(BaseModel):
    id: str  # "email:3", "file:invoices/acme_oct.md", "user"
    source: str  # human label: "Email #3 from vendor@acme-supplies.test"
    trust: Trust
    text: str
    hidden: bool = False  # True for preloaded vault values the agent never saw


class Evidence(BaseModel):
    """The passport of one argument value."""

    arg: str
    value: str  # redacted if it is a secret
    origin: Origin
    segment_id: str | None = None
    source: str | None = None
    line: int | None = None  # 1-based line inside the segment
    snippet: str | None = None
    sink: bool = True
    disguised: bool = False  # found only in a clean view ("at"/"dot", base64, Indic digits...)


class Reason(BaseModel):
    rule_id: str  # e.g. "R3_SINK_UNTRUSTED"
    verdict: Verdict
    message: str  # one plain sentence for the UI
    risk: int = 0  # 0..100
    evidence: Evidence | None = None


class Decision(BaseModel):
    id: str = Field(default_factory=lambda: new_id("dec"))
    session_id: str
    step: int
    tool: str
    args: dict[str, Any]  # secrets redacted
    verdict: Verdict
    rule_id: str  # the rule that decided the verdict
    message: str
    risk: int
    reasons: list[Reason] = []
    passports: list[Evidence] = []  # one per sink argument, for the coloured chips
    shield_on: bool = True
    executed: bool = False
    approval: Literal["approved", "rejected", "timeout"] | None = None
    ts: float = Field(default_factory=time.time)


class Capsule(BaseModel):
    """The user's intent, frozen before any untrusted content is read."""

    goal: str
    allowed_tools: list[str]
    recipients: list[str]
    files: list[str]
    max_amount_inr: int | None = None
    summary: str  # the one sentence the UI shows
    sha256: str


class Event(BaseModel):
    seq: int
    session_id: str
    type: Literal[
        "session_started",
        "capsule",
        "llm_step",
        "decision",
        "approval_needed",
        "approval_result",
        "tool_result",
        "world_event",
        "done",
        "error",
    ]
    data: dict[str, Any] = {}
    ts: float = Field(default_factory=time.time)


class ErrorBody(BaseModel):
    code: str
    message: str


class ErrorResponse(BaseModel):
    error: ErrorBody
