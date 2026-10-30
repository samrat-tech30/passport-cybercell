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

from app.api.schemas import CatalogIn, GatewayDecideIn, GatewaySessionIn, IntentIn, ObserveIn
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
    _add_catalog_segments(s)  # the rebuild must not forget the installed tools' descriptions
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


LOCKED_MESSAGE = (
    "The installed server changed its tool definitions after install (possible rug pull), "
    "so every call in this session is blocked."
)


def _r0(
    s: Session,
    tool: str,
    step: int,
    message: str = "The gate hit an error, so the call was blocked to be safe.",
) -> Decision:
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
    if run and d.shield_on:  # only an approved REQUIRE_APPROVAL gets here
        return f"PASSPORT REQUIRE_APPROVAL {d.rule_id}: approved by the user; the call may run."
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
        if s.gateway_locked:
            d, run, clean = _r0(s, body.tool, step, LOCKED_MESSAGE), False, None
            s.decisions[d.id] = d
            await s.emit("decision", d.model_dump(mode="json"))
        else:
            d, run, clean = await _decide_and_wait(s, body.tool, body.args, step)
    except Exception:  # noqa: BLE001 - fail closed: never a 500 a caller could misread
        log.exception("gateway decide failed in session %s", s.id)
        d, run, clean = _r0(s, body.tool, step), False, None
        s.decisions[d.id] = d
    d.executed = run
    if run:
        s.gateway_runs[d.id] = (body.tool, clean if clean is not None else {})
        spec = TOOLS.get(body.tool)
        if spec is None or spec.output_trust != Trust.TRUSTED:
            # Outside content is about to enter the agent's context, whether or not /observe ever
            # labels it: from now on invented values can't count as clean (red team: blind gate).
            s.gate.store.read_untrusted = True
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
        s.decisions[d.id] = d
        try:  # best effort: the stored record should say what the caller was told
            repo.save_decision(d)
        except Exception:  # noqa: BLE001
            log.exception("could not store the R0 decision in session %s", s.id)
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


def catalog_sha(tools: list[dict[str, Any]]) -> str:
    canonical = json.dumps(tools, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    return hashlib.sha256(canonical.encode()).hexdigest()


@router.post("/sessions/{session_id}/catalog", dependencies=[Depends(require_gateway_token)])
async def catalog(session_id: str, body: CatalogIn) -> dict[str, Any]:
    """The installed server's tools. Their descriptions are untrusted content (tool poisoning); the
    first catalog is pinned, and a different one later (a rug pull) locks the session."""
    s = _session(session_id)
    tools = [t.model_dump(exclude_none=True) for t in body.tools]
    try:
        for t in tools:
            _strings(t)  # every part must be labellable before anything is pinned
    except ValueError as e:
        raise _err(422, "invalid_input", f"tools: {e}") from e
    sha = catalog_sha(tools)
    if s.gateway_catalog_sha is None:
        s.gateway_catalog = {"server": body.server, "tools": tools}
        s.gateway_catalog_sha = sha
        _add_catalog_segments(s)
        s.audit(
            "gateway_catalog", {"server": body.server, "tools": [t["name"] for t in tools], "sha256": sha}
        )
        return {"sha256": sha, "tools": len(tools)}
    if sha == s.gateway_catalog_sha:
        return {"sha256": sha, "tools": len(tools)}
    s.gateway_locked = True
    s.audit(
        "gateway_catalog_changed",
        {"server": body.server, "pinned_sha256": s.gateway_catalog_sha, "new_sha256": sha},
    )
    raise _err(409, "catalog_changed", LOCKED_MESSAGE)


def _add_catalog_segments(s: Session) -> None:
    if not s.gateway_catalog:
        return
    server = s.gateway_catalog["server"]
    for t in s.gateway_catalog["tools"]:
        # The description first (evidence lines point into it), then every other string the agent
        # is shown: schema enums, defaults, examples, titles, nested and $defs parts, annotations.
        rest = {k: v for k, v in t.items() if k not in ("name", "description")}
        text = "\n".join([t["description"], *_strings(rest)])
        s.gate.store.add(
            f"tool:{t['name']}", f"Tool description: {t['name']} (server {server})", Trust.UNTRUSTED, text
        )


def _strings(value: Any, max_depth: int = 64) -> list[str]:
    """Every key and string in a JSON value, depth-first, iterative (no recursion limit to hit).
    Deeper than max_depth raises ValueError: /catalog refuses it rather than leave a part unlabelled."""
    out: list[str] = []
    stack: list[tuple[Any, int]] = [(value, 0)]
    while stack:
        v, depth = stack.pop()
        if depth > max_depth:
            raise ValueError(f"tool definition nested deeper than {max_depth} levels")
        if isinstance(v, dict):
            for k, x in reversed(list(v.items())):
                stack.append((x, depth + 1))
                stack.append((str(k), depth + 1))
        elif isinstance(v, list):
            stack.extend((x, depth + 1) for x in reversed(v))
        elif isinstance(v, str):
            out.append(v)
        elif v is not None and not isinstance(v, bool):
            out.append(str(v))
    return out


@router.post("/sessions/{session_id}/observe", dependencies=[Depends(require_gateway_token)])
async def observe(session_id: str, body: ObserveIn) -> dict[str, Any]:
    s = _session(session_id)
    entry = s.gateway_runs.get(body.decision_id)
    if entry is None or body.decision_id in s.gateway_observed:
        s.audit("gateway_observe_rejected", {"decision_id": body.decision_id[:40]})
        raise _err(409, "observe_rejected", "Output can be reported once, only for a call this session ran.")
    s.gateway_observed.add(body.decision_id)
    tool, args = entry
    _ingest(s, body.decision_id, tool, args, body.output)
    preview = s.world.redact(body.output)[:300]
    await s.emit("tool_result", {"decision_id": body.decision_id, "executed": True, "preview": preview})
    return {"ok": True}


def _ingest(s: Session, decision_id: str, tool: str, args: dict[str, Any], output: str) -> None:
    """Label upstream output. Trust comes from the tool registry by name, never from the caller.

    The upstream is not PASSPORT's World, so nothing it returns is a fixed confirmation: every byte
    the agent sees is stored, at the tool's trust capped to UNTRUSTED, under an id unique to this
    decision (a re-read with new content, or fields we don't parse, are never dropped).
    """
    store = s.gate.store
    spec = TOOLS.get(tool)
    trust = spec.output_trust if spec and spec.output_trust != Trust.TRUSTED else Trust.UNTRUSTED
    if spec is not None:
        if tool == "read_secret" and isinstance(args.get("key"), str) and len(output) >= 6:
            key = args["key"]
            if s.world.vault.get(key) not in (None, output):
                key = f"{key}_UPSTREAM_{decision_id[-6:]}"  # never replace a canary or an earlier read
            s.world.vault[key] = output  # redaction and R2/R4 cover every value seen
        try:
            # Parsed first, so evidence points at the email/file line when the value is in there.
            parsed: Any = json.loads(output) if tool in ("list_unread_emails", "read_email") else output
            if spec.output_trust != Trust.TRUSTED:
                store.ingest(tool, args, parsed)
        except (ValueError, KeyError, TypeError, AttributeError, RecursionError):
            pass  # not the shape we expect: the raw segment below still labels all of it
    name = tool[:64]
    store.add(f"{name}:out:{decision_id}", f"{name} output", trust, output, hidden=trust == Trust.SECRET)
    if tool == "read_secret" and isinstance(args.get("key"), str):
        seg = store.get(f"secret:{args['key']}")
        if seg is not None:
            seg.hidden = True  # never served by /segments or quoted as an evidence snippet
