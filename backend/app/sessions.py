"""One agent run = one Session: its world, its segment store, its frozen intent, its event stream.

Sessions live in memory (bounded) while they run; their decisions, world events and audit rows
are written to SQLite so nothing important is lost on a restart.
"""

from __future__ import annotations

import asyncio
from collections import OrderedDict
from dataclasses import dataclass, field
from typing import Any, Literal

from app.agent.llm import LLM, OpenAICompatLLM, ReplayLLM
from app.agent.recorder import Recorder
from app.config import Settings
from app.contracts import Decision, new_id
from app.db import audit, repo
from app.events import Bus
from app.gate.capsule import build_capsule
from app.gate.decide import GateContext
from app.gate.policy import load_policy
from app.gate.segments import new_store
from app.scenarios import FIXTURES_DIR, Scenario
from app.tools.world import World

ApprovalMode = Literal["interactive", "approve", "reject", "timeout"]
MAX_SESSIONS_IN_MEMORY = 200


@dataclass
class Session:
    id: str
    scenario: Scenario | None
    user_request: str
    shield_on: bool
    mode: Literal["replay", "live", "gateway"]
    world: World
    gate: GateContext
    llm: LLM | None  # None for gateway sessions: the agent runs elsewhere
    bus: Bus
    approval_mode: ApprovalMode
    approval_timeout_s: int
    max_steps: int
    persist: bool = True
    recorder: Recorder | None = None
    status: str = "created"
    decisions: dict[str, Decision] = field(default_factory=dict)
    # Gateway sessions only: decision id -> (tool, validated args) for calls answered run=true,
    # and the ids whose output was already observed (once per decision).
    gateway_runs: dict[str, tuple[str, dict[str, Any]]] = field(default_factory=dict)
    gateway_observed: set[str] = field(default_factory=set)
    _world_events_saved: int = 0

    async def emit(self, type_: str, data: dict[str, Any] | None = None) -> None:
        await self.bus.emit(type_, data)

    def set_status(self, status: str) -> None:
        self.status = status
        if self.persist:
            repo.set_session_status(self.id, status)

    def audit(self, kind: str, data: dict[str, Any]) -> None:
        if self.persist:
            audit.append(kind, data, session_id=self.id)

    async def flush_world_events(self) -> None:
        """Persist + stream world events produced by the last tool run."""
        new = self.world.events[self._world_events_saved :]
        self._world_events_saved = len(self.world.events)
        for e in new:
            if self.persist:
                repo.add_world_event(self.id, e["kind"], e["data"])
            if e["kind"] == "attacker_received":
                self.audit("attacker_received", e["data"])
            await self.emit("world_event", e)

    async def ask_approval(self, d: Decision) -> Literal["approved", "rejected", "timeout"]:
        if self.approval_mode == "approve":
            return "approved"
        if self.approval_mode == "reject":
            return "rejected"
        if self.approval_mode == "timeout":
            return "timeout"
        fut: asyncio.Future[bool] = asyncio.get_running_loop().create_future()
        PENDING[d.id] = (self.id, fut)
        self.set_status("waiting_approval")
        await self.emit("approval_needed", d.model_dump(mode="json"))
        try:
            approved = await asyncio.wait_for(fut, timeout=self.approval_timeout_s)
            return "approved" if approved else "rejected"
        except TimeoutError:
            return "timeout"  # fail closed: no answer means no
        finally:
            PENDING.pop(d.id, None)
            self.set_status("running")


SESSIONS: OrderedDict[str, Session] = OrderedDict()
PENDING: dict[str, tuple[str, asyncio.Future]] = {}


def create_session(
    settings: Settings,
    *,
    scenario: Scenario | None,
    user_request: str | None,
    shield_on: bool,
    mode: Literal["replay", "live"],
    approval_mode: ApprovalMode = "interactive",
    persist: bool = True,
    llm: LLM | None = None,  # tests inject a fake-client OpenAICompatLLM here
) -> Session:
    if mode == "replay" and scenario is None:
        raise ValueError("replay mode needs a scenario (its recorded plan)")
    request = (user_request or (scenario.user_request if scenario else "")).strip()
    if not request:
        raise ValueError("user_request is empty")
    world = World(**scenario.world.model_dump()) if scenario else World()
    policy = load_policy()
    sid = new_id("ses")
    store = new_store(request, world)
    capsule = build_capsule(request)
    gate = GateContext(
        session_id=sid,
        policy=policy,
        store=store,
        capsule=capsule,
        world=world,
        profile=policy.default_profile,
        fault=scenario.fault if scenario else None,
    )
    if llm is None:
        llm = ReplayLLM(scenario.script) if mode == "replay" else OpenAICompatLLM(settings)
    recorder = None
    if mode == "live" and settings.record_fixtures:
        recorder = Recorder(FIXTURES_DIR, scenario.id if scenario else None, settings.llm_model, shield_on)
    s = Session(
        id=sid,
        scenario=scenario,
        user_request=request,
        shield_on=shield_on,
        mode=mode,
        world=world,
        gate=gate,
        llm=llm,
        bus=Bus(sid),
        approval_mode=approval_mode,
        approval_timeout_s=settings.approval_timeout_s,
        max_steps=settings.max_agent_steps,
        persist=persist,
        recorder=recorder,
    )
    if persist:
        repo.create_session(sid, scenario.id if scenario else None, request, shield_on, mode)
        repo.set_session_capsule(sid, capsule.model_dump())
    SESSIONS[sid] = s
    _evict()
    return s


def create_gateway_session(settings: Settings, *, agent_name: str, client: str, shield_on: bool) -> Session:
    """A session driven by an outside agent through the MCP gateway (contracts/README.md "Gateway API").

    No LLM and no agent loop. Its World is used only for redaction and the vault: tools run upstream,
    never here. The intent (capsule + USER segment) arrives later with the first start_task.
    """
    world = World()
    policy = load_policy()
    sid = new_id("ses")
    gate = GateContext(
        session_id=sid,
        policy=policy,
        store=new_store("", world),
        capsule=build_capsule(""),
        world=world,
        profile=policy.default_profile,
    )
    s = Session(
        id=sid,
        scenario=None,
        user_request="",
        shield_on=shield_on,
        mode="gateway",
        world=world,
        gate=gate,
        llm=None,
        bus=Bus(sid),
        approval_mode="interactive",
        approval_timeout_s=settings.gateway_approval_wait_s,
        max_steps=0,
    )
    repo.create_gateway_session(sid, agent_name, client, shield_on)
    SESSIONS[sid] = s
    _evict()
    return s


def _evict() -> None:
    """Keep memory bounded, oldest first, but never drop a gateway session: its client (Claude
    Desktop) lives for hours and would get 404 for every call from then on."""
    excess = len(SESSIONS) - MAX_SESSIONS_IN_MEMORY
    for sid in [k for k, v in SESSIONS.items() if v.mode != "gateway"][: max(0, excess)]:
        del SESSIONS[sid]


def resolve_approval(decision_id: str, approve: bool) -> bool:
    entry = PENDING.get(decision_id)
    if not entry or entry[1].done():
        return False
    entry[1].set_result(approve)
    return True
