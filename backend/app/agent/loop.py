"""The agent loop. Plain Python, no framework: ask the LLM, send every tool call through the gate,
feed results back, stop when the model stops calling tools or the step limit is hit."""

from __future__ import annotations

import logging
from typing import Any

from app.agent.llm import LLMError, assistant_message
from app.agent.prompts import NAIVE_ASSISTANT_PROMPT
from app.gate.handle import handle
from app.sessions import Session
from app.tools.registry import openai_tool_schemas

log = logging.getLogger("passport.agent")


async def run_session(s: Session) -> None:
    s.set_status("running")
    s.audit(
        "session_started",
        {
            "user_request": s.user_request,
            "shield_on": s.shield_on,
            "mode": s.mode,
            "scenario_id": s.scenario.id if s.scenario else None,
            "capsule_sha256": s.gate.capsule.sha256,
        },
    )
    await s.emit(
        "session_started",
        {
            "user_request": s.user_request,
            "shield_on": s.shield_on,
            "mode": s.mode,
            "scenario_id": s.scenario.id if s.scenario else None,
        },
    )
    await s.emit("capsule", s.gate.capsule.model_dump())

    messages: list[dict[str, Any]] = [
        {"role": "system", "content": NAIVE_ASSISTANT_PROMPT},
        {"role": "user", "content": s.user_request},
    ]
    tools = openai_tool_schemas()
    try:
        for step in range(1, s.max_steps + 1):
            turn = await s.llm.next_turn(messages, tools, s)
            if s.recorder:
                s.recorder.add(turn, s.world)
            await s.emit(
                "llm_step",
                {
                    "step": step,
                    "content": s.world.redact(turn.content or ""),
                    "tool_calls": [{"name": c.name, "args": s.world.redact(c.args)} for c in turn.tool_calls],
                },
            )
            if not turn.tool_calls:
                await _finish(s, "done", {"answer": s.world.redact(turn.content or "")})
                return
            messages.append(assistant_message(turn))
            for call in turn.tool_calls:
                result = await handle(s, call.name, call.args, step)
                messages.append({"role": "tool", "tool_call_id": call.id, "content": result})
        await _finish(s, "done", {"answer": "Stopped: step limit reached."})
    except LLMError as e:
        log.warning("session %s: live LLM failed: %s", s.id, e)
        await _finish(s, "error", {"message": f"The agent stopped: {e}"})
    except Exception as e:  # noqa: BLE001 - never leak a stack trace to the UI
        log.exception("session %s failed", s.id)
        await _finish(s, "error", {"message": f"The agent stopped because of an error ({type(e).__name__})."})


async def _finish(s: Session, status: str, data: dict[str, Any]) -> None:
    if s.recorder:
        try:
            path = s.recorder.save(s.id, status)
            log.info("session %s recorded to %s", s.id, path.name)
        except OSError:
            log.exception("session %s: could not save the fixture", s.id)
    s.set_status(status)
    s.audit("session_" + status, data)
    await s.emit(status, data)
