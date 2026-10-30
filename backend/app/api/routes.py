"""All HTTP routes. Thin: validate input, call the session/gate/db modules, shape the reply
exactly as contracts/README.md says."""

from __future__ import annotations

import asyncio
import json
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from fastapi.responses import StreamingResponse

from app import __version__
from app.agent.loop import run_session
from app.api.schemas import ApprovalIn, DecideIn, NewSessionIn
from app.config import get_settings
from app.contracts import Trust, new_id
from app.db import audit, repo
from app.eval_runner import run_eval
from app.gate.capsule import build_capsule
from app.gate.decide import GateContext, decide
from app.gate.policy import load_policy
from app.gate.segments import SegmentStore
from app.scenarios import load_scenarios
from app.security import rate_limit, require_access
from app.sessions import PENDING, SESSIONS, create_session, resolve_approval
from app.tools.world import World

router = APIRouter()
_BACKGROUND: set[asyncio.Task] = set()


def _err(status: int, code: str, message: str) -> HTTPException:
    return HTTPException(status_code=status, detail={"code": code, "message": message})


@router.get("/health")
def health() -> dict[str, Any]:
    s = get_settings()
    return {
        "status": "ok",
        "version": __version__,
        "env": s.app_env,
        "live_llm_available": s.live_llm_ready,
        "access_code_required": s.demo_access_code is not None,
    }


@router.get("/scenarios")
def scenarios() -> list[dict[str, Any]]:
    return [
        {
            "id": sc.id,
            "title": sc.title,
            "category": sc.category,
            "user_request": sc.user_request,
            "is_attack": sc.is_attack,
            "v2_note": sc.v2_note,
        }
        for sc in load_scenarios().values()
    ]


@router.post(
    "/sessions", status_code=201, dependencies=[Depends(require_access), Depends(rate_limit("sessions"))]
)
async def new_session(body: NewSessionIn) -> dict[str, Any]:
    settings = get_settings()
    sc = None
    if body.scenario_id:
        sc = load_scenarios().get(body.scenario_id)
        if sc is None:
            raise _err(404, "scenario_not_found", f"No scenario {body.scenario_id}.")
    if body.mode == "live" and not settings.live_llm_ready:
        raise _err(
            400, "live_llm_disabled", "Live LLM mode is not configured on this server. Use replay mode."
        )
    if body.mode == "replay" and sc is None:
        raise _err(400, "scenario_required", "Replay mode needs a scenario_id.")
    if body.mode == "replay" and body.user_request and body.user_request.strip() != sc.user_request:
        raise _err(400, "request_mismatch", "In replay mode the request must be the scenario's own request.")
    try:
        s = create_session(
            settings, scenario=sc, user_request=body.user_request, shield_on=body.shield_on, mode=body.mode
        )
    except ValueError as e:
        raise _err(400, "invalid_session", str(e)) from e
    task = asyncio.create_task(run_session(s))
    _BACKGROUND.add(task)
    task.add_done_callback(_BACKGROUND.discard)
    return {
        "session_id": s.id,
        "status": s.status,
        "capsule": s.gate.capsule.model_dump(),
        "shield_on": s.shield_on,
        "mode": s.mode,
    }


@router.get("/sessions/{session_id}")
def get_session(session_id: str) -> dict[str, Any]:
    row = repo.get_session(session_id)
    if row is None:
        raise _err(404, "session_not_found", "No such session.")
    pending = [
        d.model_dump(mode="json")
        for did, (sid, _) in list(PENDING.items())
        if sid == session_id and sid in SESSIONS
        for d in [SESSIONS[sid].decisions.get(did)]
        if d
    ]
    return {
        "session": row,
        "decisions": repo.list_decisions(session_id),
        "world_events": repo.list_world_events(session_id=session_id),
        "pending_approvals": pending,
    }


@router.get("/sessions/{session_id}/events")
async def events(request: Request, session_id: str, after: int = Query(0, ge=0)) -> StreamingResponse:
    # Browsers send Last-Event-ID when they reconnect; resume from there so nothing repeats.
    last = request.headers.get("last-event-id", "")
    after = max(after, int(last)) if last.isdigit() else after
    s = SESSIONS.get(session_id)
    if s is None:
        raise _err(404, "stream_not_available", "This session is not running on this server any more.")

    async def gen():
        async for ev in s.bus.stream(after=after):
            if ev is None:
                yield ": keep-alive\n\n"
            else:
                yield f"id: {ev.seq}\nevent: {ev.type}\ndata: {json.dumps(ev.model_dump(mode='json'), ensure_ascii=False)}\n\n"

    return StreamingResponse(
        gen(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


@router.get("/sessions/{session_id}/segments/{segment_id:path}")
def segment(session_id: str, segment_id: str) -> dict[str, Any]:
    s = SESSIONS.get(session_id)
    seg = s.gate.store.get(segment_id) if s else None
    if s is None or seg is None or seg.hidden:
        raise _err(404, "segment_not_found", "No such source in this session.")
    text = s.world.redact(seg.text)
    return {
        "id": seg.id,
        "source": seg.source,
        "trust": seg.trust.value,
        "text": text,
        "lines": text.splitlines(),
    }


@router.post("/approvals/{decision_id}", dependencies=[Depends(require_access)])
def approve(decision_id: str, body: ApprovalIn) -> dict[str, Any]:
    if not resolve_approval(decision_id, body.approve):
        raise _err(404, "approval_not_pending", "This approval is not waiting any more.")
    return {"ok": True, "decision_id": decision_id, "approved": body.approve}


@router.get("/attacker")
def attacker(session_id: str | None = Query(None, max_length=40)) -> dict[str, Any]:
    return {"items": repo.list_world_events(session_id=session_id, kind="attacker_received", limit=100)}


@router.get("/audit")
def audit_list(
    limit: int = Query(100, ge=1, le=500), session_id: str | None = Query(None, max_length=40)
) -> dict[str, Any]:
    return {"items": audit.recent(limit=limit, session_id=session_id)}


@router.get("/audit/verify")
def audit_verify() -> dict[str, Any]:
    return audit.verify()


@router.post("/eval/run", dependencies=[Depends(require_access), Depends(rate_limit("eval"))])
async def eval_run() -> dict[str, Any]:
    summary, rows = await run_eval(persist=True)
    return {"summary": summary, "rows": rows}


@router.get("/eval/latest")
def eval_latest() -> dict[str, Any]:
    run = repo.latest_eval_run()
    if run is None:
        raise _err(404, "no_eval_yet", "No evaluation has been run yet.")
    return run


@router.post("/v1/decide", dependencies=[Depends(require_access), Depends(rate_limit("decide"))])
def v1_decide(body: DecideIn) -> dict[str, Any]:
    """Integration endpoint: any framework can ask PASSPORT for a verdict before running a tool."""
    world = World()
    world.vault = {
        f"SECRET_{i}": c.text for i, c in enumerate(body.context) if c.trust == "secret" and len(c.text) >= 6
    }
    store = SegmentStore()
    store.add("user", "Your request", Trust.USER, body.user_request)
    for i, c in enumerate(body.context):
        store.add(f"ctx:{i}", c.source, Trust(c.trust), c.text, hidden=c.trust == "secret")
    policy = load_policy()
    ctx = GateContext(
        session_id=new_id("api"),
        policy=policy,
        store=store,
        capsule=build_capsule(body.user_request),
        world=world,
        profile=policy.default_profile,
    )
    d = decide(ctx, body.tool, body.args, step=1)
    audit.append(
        "v1_decide", {"tool": d.tool, "verdict": d.verdict.value, "rule_id": d.rule_id, "args": d.args}
    )
    return d.model_dump(mode="json")


@router.post("/admin/reset", dependencies=[Depends(require_access)])
def admin_reset() -> dict[str, Any]:
    repo.clear_demo_data()
    SESSIONS.clear()
    return {"ok": True, "note": "Sessions and world events cleared. The audit log is never deleted."}
