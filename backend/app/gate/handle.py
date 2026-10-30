"""decide -> (approve) -> execute -> label -> log. The ONLY place a tool function is ever called."""

from __future__ import annotations

import json
from typing import TYPE_CHECKING, Any

from app.contracts import Verdict
from app.db import repo
from app.gate.decide import decide
from app.tools.registry import InvalidArgs, run_tool, validate_args
from app.tools.world import ToolError

if TYPE_CHECKING:
    from app.sessions import Session

MAX_RESULT_CHARS = 6000


async def handle(s: Session, tool: str, raw_args: Any, step: int) -> str:
    """Run one proposed tool call through PASSPORT. Returns the text the agent sees next."""
    d = decide(s.gate, tool, raw_args, step)
    d.shield_on = s.shield_on
    s.decisions[d.id] = d
    await s.emit("decision", d.model_dump(mode="json"))

    if not s.shield_on:
        run = True  # shield OFF: decision is logged ("would have blocked") but the call runs anyway
    elif d.verdict == Verdict.ALLOW:
        run = True
    elif d.verdict == Verdict.REQUIRE_APPROVAL:
        d.approval = await s.ask_approval(d)
        s.audit("approval", {"decision_id": d.id, "result": d.approval})
        await s.emit("approval_result", {"decision_id": d.id, "result": d.approval})
        run = d.approval == "approved"
    else:
        run = False

    result: str
    if run:
        try:
            args = validate_args(tool, raw_args)
            output = run_tool(s.world, tool, args)
            s.gate.store.ingest(tool, args, output)  # label the output BEFORE the agent sees it
            d.executed = True
            result = output if isinstance(output, str) else json.dumps(output, ensure_ascii=False)
        except (InvalidArgs, ToolError) as e:
            result = f"Error: {e}"
        await s.flush_world_events()
    elif d.approval in ("rejected", "timeout"):
        result = f"Not done: the user did not approve this ({d.message})"
    else:
        result = f"Blocked by PASSPORT ({d.rule_id}): {d.message}"

    if s.persist:
        repo.save_decision(d)
    s.audit(
        "decision",
        {
            "decision_id": d.id,
            "step": step,
            "tool": d.tool,
            "args": d.args,
            "verdict": d.verdict.value,
            "rule_id": d.rule_id,
            "rules": [r.rule_id for r in d.reasons],
            "shield_on": d.shield_on,
            "executed": d.executed,
            "approval": d.approval,
        },
    )
    await s.emit("decision", d.model_dump(mode="json"))  # updated: executed / approval
    await s.emit(
        "tool_result", {"decision_id": d.id, "executed": d.executed, "preview": s.world.redact(result)[:300]}
    )
    return result[:MAX_RESULT_CHARS]
