"""Gateway API: the backend half of the MCP gateway (contracts/README.md "Gateway API").

An outside agent (Claude Desktop, fooled_agent.py...) talks MCP to integrations/passport_gateway,
which asks these routes before every tool call. The gate decides here; the tool runs upstream only
when we answer run=true, and its output comes back through /observe so later decisions can trace
values to it. No tool ever runs in the backend for these sessions.
"""

from __future__ import annotations

import hashlib
import hmac
import json
import logging
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Request

from app.api.schemas import GatewayDecideIn, GatewaySessionIn, IntentIn, ObserveIn
from app.config import get_settings
from app.contracts import Decision, Reason, Trust, Verdict
from app.db import repo
from app.gate.capsule import build_capsule
from app.gate.decide import decide
from app.gate.segments import new_store
from app.security import limiter
from app.sessions import SESSIONS, Session, create_gateway_session
from app.tools.registry import TOOLS, InvalidArgs, validate_args

log = logging.getLogger("passport.gateway")
router = APIRouter(prefix="/v1/gateway")


def _err(status: int, code: str, message: str) -> HTTPException:
    return HTTPException(status_code=status, detail={"code": code, "message": message})


def gateway_enabled() -> None:
    if get_settings().gateway_token is None:
        raise _err(503, "gateway_disabled", "The gateway API is off on this server (no gateway token set).")


def require_gateway_token(request: Request) -> None:
    """Fail closed: no token configured → 503 for everything; wrong or missing header → 401."""
    gateway_enabled()
    token = get_settings().gateway_token or ""
    given = request.headers.get("x-gateway-token", "")
    if not hmac.compare_digest(given.encode(), token.encode()):
        raise _err(401, "gateway_unauthorized", "Missing or wrong gateway token.")
    key = "gw:" + hashlib.sha256(token.encode()).hexdigest()[:16]
    limiter.check(key, "gateway", get_settings().gateway_rate_limit_per_min)


def _session(session_id: str) -> Session:
    s = SESSIONS.get(session_id)
    if s is None or s.mode != "gateway":
        raise _err(404, "session_not_found", "No such gateway session.")
    return s


@router.post("/sessions", status_code=201, dependencies=[Depends(require_gateway_token)])
async def new_gateway_session(body: GatewaySessionIn) -> dict[str, Any]:
    s = create_gateway_session(
        get_settings(), agent_name=body.agent_name, client=body.client, shield_on=body.shield_on
    )
    s.audit(
        "gateway_session", {"agent_name": body.agent_name, "client": body.client, "shield_on": s.shield_on}
    )
    return {"session_id": s.id}


@router.get("/sessions", dependencies=[Depends(gateway_enabled)])
def list_gateway_sessions() -> dict[str, Any]:
    return {"items": repo.list_gateway_sessions()}


@router.post("/sessions/{session_id}/intent", dependencies=[Depends(require_gateway_token)])
async def intent(session_id: str, body: IntentIn) -> dict[str, Any]:
    s = _session(session_id)
    if s.user_request:
        s.audit("gateway_intent_rejected", {"reason": "intent already locked"})
        raise _err(409, "intent_locked", "The intent of this session is already locked.")
    request = body.request.strip()
    if not request:
        raise _err(422, "invalid_input", "request: must not be blank")
    s.user_request = request
    # Nothing has entered the store yet (decide is refused before the intent), so rebuild it.
    s.gate.store = new_store(request, s.world)
    s.gate.capsule = build_capsule(request)
    repo.set_session_request(s.id, request)
    repo.set_session_capsule(s.id, s.gate.capsule.model_dump())
    s.set_status("running")
    s.audit(
        "session_started",
        {
            "user_request": request,
            "shield_on": s.shield_on,
            "mode": "gateway",
            "capsule_sha256": s.gate.capsule.sha256,
        },
    )
    await s.emit(
        "session_started",
        {"user_request": request, "shield_on": s.shield_on, "mode": "gateway", "scenario_id": None},
    )
    await s.emit("capsule", s.gate.capsule.model_dump())
    return {"capsule": s.gate.capsule.model_dump()}


def _r0(s: Session, tool: str, step: int) -> Decision:
    message = "The gate hit an error, so the call was blocked to be safe."
    risk = s.gate.policy.risk.get("R0_FAIL_CLOSED", 100)
    return Decision(
        session_id=s.id,
        step=step,
        tool=str(tool)[:64],
        args={},
        verdict=Verdict.DENY,
        rule_id="R0_FAIL_CLOSED",
        message=message,
        risk=risk,
        reasons=[Reason(rule_id="R0_FAIL_CLOSED", verdict=Verdict.DENY, message=message, risk=risk)],
        shield_on=s.shield_on,
    )


def _agent_message(d: Decision, run: bool) -> str:
    if run and d.verdict == Verdict.ALLOW:
        return "PASSPORT ALLOW: the call may run."
    if run:
        return f"PASSPORT monitor mode: would be {d.verdict.value} {d.rule_id} ({d.message}); the call runs anyway."
    if d.approval in ("rejected", "timeout"):
        return f"PASSPORT REQUIRE_APPROVAL {d.rule_id}: not approved ({d.approval}). {d.message}"
    return f"PASSPORT {d.verdict.value} {d.rule_id}: {d.message}"


@router.post("/sessions/{session_id}/decide", dependencies=[Depends(require_gateway_token)])
async def gateway_decide(session_id: str, body: GatewayDecideIn) -> dict[str, Any]:
    s = _session(session_id)
    if not s.user_request:
        raise _err(409, "intent_required", "Call start_task with the user's request first.")
    step = len(s.decisions) + 1
    try:
        d, run, clean = await _decide_and_wait(s, body.tool, body.args, step)
    except Exception:  # noqa: BLE001 - fail closed: never a 500 a caller could misread
        log.exception("gateway decide failed in session %s", s.id)
        d, run, clean = _r0(s, body.tool, step), False, None
        s.decisions[d.id] = d
    d.executed = run
    if run:
        s.gateway_runs[d.id] = (body.tool, clean if clean is not None else {})
    message = _agent_message(d, run)
    try:
        repo.save_decision(d)
        s.audit(
            "gateway_decide",
            {
                "decision_id": d.id,
                "step": step,
                "tool": d.tool,
                "args": d.args,
                "verdict": d.verdict.value,
                "rule_id": d.rule_id,
                "shield_on": d.shield_on,
                "approval": d.approval,
                "run": run,
            },
        )
        await s.emit("decision", d.model_dump(mode="json"))
        await s.emit("gateway_call", {"decision_id": d.id, "run": run, "message": s.world.redact(message)})
    except Exception:  # noqa: BLE001 - logging must not turn into a run the caller did not get told about
        log.exception("gateway decide bookkeeping failed in session %s", s.id)
        s.gateway_runs.pop(d.id, None)
        d, run = _r0(s, body.tool, step), False
        message = _agent_message(d, run)
    return {"decision": d.model_dump(mode="json"), "run": run, "message": message}


async def _decide_and_wait(
    s: Session, tool: str, raw_args: dict[str, Any], step: int
) -> tuple[Decision, bool, dict[str, Any] | None]:
    d = decide(s.gate, tool, raw_args, step)
    d.shield_on = s.shield_on
    s.decisions[d.id] = d
    await s.emit("decision", d.model_dump(mode="json"))
    if not s.shield_on:
        run = True  # monitor mode: the decision shows what would have happened
    elif d.verdict == Verdict.ALLOW:
        run = True
    elif d.verdict == Verdict.REQUIRE_APPROVAL:
        d.approval = await s.ask_approval(d)  # waits ≤ GATEWAY_APPROVAL_WAIT_S; no answer = no
        s.audit("approval", {"decision_id": d.id, "result": d.approval})
        await s.emit("approval_result", {"decision_id": d.id, "result": d.approval})
        run = d.approval == "approved"
    else:
        run = False
    clean = None
    if run:
        try:
            clean = validate_args(tool, raw_args)
        except InvalidArgs:
            clean = None  # only reachable in monitor mode (the gate already DENYs invalid args)
    return d, run, clean


@router.post("/sessions/{session_id}/observe", dependencies=[Depends(require_gateway_token)])
async def observe(session_id: str, body: ObserveIn) -> dict[str, Any]:
    s = _session(session_id)
    entry = s.gateway_runs.get(body.decision_id)
    if entry is None or body.decision_id in s.gateway_observed:
        s.audit("gateway_observe_rejected", {"decision_id": body.decision_id[:40]})
        raise _err(409, "observe_rejected", "Output can be reported once, only for a call this session ran.")
    s.gateway_observed.add(body.decision_id)
    tool, args = entry
    _ingest(s, tool, args, body.output)
    preview = s.world.redact(body.output)[:300]
    await s.emit("tool_result", {"decision_id": body.decision_id, "executed": True, "preview": preview})
    return {"ok": True}


def _ingest(s: Session, tool: str, args: dict[str, Any], output: str) -> None:
    """Label upstream output. Trust comes from the tool registry by name, never from the caller."""
    store = s.gate.store
    spec = TOOLS.get(tool)
    if spec is None:
        store.add(f"{tool[:64]}:{len(store.items)}", f"{tool[:64]} output", Trust.UNTRUSTED, output)
        return
    if tool == "read_secret" and isinstance(args.get("key"), str):
        if len(output) >= 6:
            s.world.vault[args["key"]] = output  # redaction and R4 cover the real upstream value
    try:
        parsed: Any = json.loads(output) if tool in ("list_unread_emails", "read_email") else output
        store.ingest(tool, args, parsed)
    except (ValueError, KeyError, TypeError, AttributeError):
        # Not the shape we expect: keep it, at the tool's trust (or lower), as one plain segment.
        trust = spec.output_trust if spec.output_trust != Trust.TRUSTED else Trust.UNTRUSTED
        store.add(f"{tool}:{len(store.items)}", f"{tool} output", trust, output)
