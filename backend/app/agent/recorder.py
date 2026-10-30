"""Record a live session's assistant turns as a replay fixture (RECORD_FIXTURES=1).

The file holds a `script` in the same shape as a scenario YAML's, so a scenario can replay it with
`script_file: fixtures/<name>.json`. Secret values (in every encoding the world knows) are written
as {{secret:NAME[:enc]}} templates, never as values: ReplayLLM fills them back in only if the
replayed session has really read that secret.
"""

from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path
from typing import TYPE_CHECKING, Any

from app.agent.llm import SECRET_ENCODINGS, LLMTurn

if TYPE_CHECKING:
    from app.tools.world import World


def template_secrets(value: Any, world: World) -> Any:
    if isinstance(value, str):
        forms = [
            (enc_fn(secret), name, enc)
            for name, secret in world.vault.items()
            for enc, enc_fn in SECRET_ENCODINGS.items()
        ]
        for form, name, enc in sorted(forms, key=lambda f: len(f[0]), reverse=True):
            if form and form in value:
                tag = f"{{{{secret:{name}}}}}" if enc == "raw" else f"{{{{secret:{name}:{enc}}}}}"
                value = value.replace(form, tag)
        return value
    if isinstance(value, dict):
        return {k: template_secrets(v, world) for k, v in value.items()}
    if isinstance(value, list):
        return [template_secrets(v, world) for v in value]
    return value


class Recorder:
    def __init__(self, out_dir: Path, scenario_id: str | None, model: str | None, shield_on: bool) -> None:
        self.out_dir = out_dir
        self.scenario_id = scenario_id or "free"
        self.model = model
        self.shield_on = shield_on
        self.steps: list[dict[str, Any]] = []

    def add(self, turn: LLMTurn, world: World) -> None:
        step: dict[str, Any] = {}
        if turn.content:
            step["say"] = template_secrets(turn.content, world)
        if turn.tool_calls:
            # invalid-JSON args stay a raw string, so the replay gets the same R0 DENY
            step["calls"] = [
                {"name": c.name, "args": template_secrets(c.args, world)} for c in turn.tool_calls
            ]
        self.steps.append(step)

    def save(self, session_id: str, status: str) -> Path:
        now = datetime.now(UTC)
        # session id suffix: two runs in the same second must not overwrite each other
        path = self.out_dir / f"{self.scenario_id}_{now:%Y%m%dT%H%M%SZ}_{session_id[-6:]}.json"
        doc = {
            "scenario_id": self.scenario_id,
            "model": self.model,
            "shield_on": self.shield_on,
            "status": status,
            "recorded_at": now.isoformat(timespec="seconds"),
            "script": self.steps,
        }
        self.out_dir.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(doc, indent=2, ensure_ascii=False) + "\n", encoding="utf-8", newline="\n")
        return path
