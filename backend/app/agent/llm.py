"""LLM back-ends behind one tiny interface: next_turn(messages, tools, session) -> LLMTurn.

* ReplayLLM: returns a recorded/scripted plan of tool calls (from the scenario YAML). Used for the
  stage demo, the eval and tests: no network, same result every time. The GATE still runs live.
* OpenAICompatLLM: any OpenAI-compatible chat API (Groq, OpenRouter, Ollama, OpenAI...).
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any, Protocol

from app.config import Settings

if TYPE_CHECKING:
    from app.sessions import Session

_SECRET_TMPL = re.compile(r"\{\{secret:([A-Z0-9_]+)\}\}")


@dataclass
class ToolCallReq:
    id: str
    name: str
    args: Any  # dict normally; a raw string if the model produced invalid JSON (gate denies it)


@dataclass
class LLMTurn:
    content: str | None
    tool_calls: list[ToolCallReq] = field(default_factory=list)


class LLM(Protocol):
    async def next_turn(
        self, messages: list[dict[str, Any]], tools: list[dict[str, Any]], session: Session
    ) -> LLMTurn: ...


class ReplayLLM:
    def __init__(self, steps: list[dict[str, Any]]) -> None:
        self.steps = steps
        self.i = 0

    def _resolve(self, value: Any, session: Session) -> Any:
        # A scripted agent can only use a secret it has actually seen in this session.
        if isinstance(value, str):

            def sub(m: re.Match) -> str:
                name = m.group(1)
                return session.world.vault[name] if name in session.gate.store.revealed else "[unknown]"

            return _SECRET_TMPL.sub(sub, value)
        if isinstance(value, dict):
            return {k: self._resolve(v, session) for k, v in value.items()}
        if isinstance(value, list):
            return [self._resolve(v, session) for v in value]
        return value

    async def next_turn(self, messages, tools, session) -> LLMTurn:
        if self.i >= len(self.steps):
            return LLMTurn(content="Done.")
        step = self.steps[self.i]
        self.i += 1
        calls = [
            ToolCallReq(
                id=f"call_{self.i}_{j}", name=c["name"], args=self._resolve(c.get("args", {}), session)
            )
            for j, c in enumerate(step.get("calls", []))
        ]
        return LLMTurn(content=step.get("say"), tool_calls=calls)


def parse_openai_message(msg: Any) -> LLMTurn:
    calls = []
    for tc in getattr(msg, "tool_calls", None) or []:
        raw = tc.function.arguments or "{}"
        try:
            args = json.loads(raw)
        except json.JSONDecodeError:
            args = raw  # the gate turns this into R0_FAIL_CLOSED
        calls.append(ToolCallReq(id=tc.id, name=tc.function.name, args=args))
    return LLMTurn(content=getattr(msg, "content", None), tool_calls=calls)


def assistant_message(turn: LLMTurn) -> dict[str, Any]:
    msg: dict[str, Any] = {"role": "assistant", "content": turn.content or ""}
    if turn.tool_calls:
        msg["tool_calls"] = [
            {
                "id": c.id,
                "type": "function",
                "function": {
                    "name": c.name,
                    "arguments": c.args if isinstance(c.args, str) else json.dumps(c.args),
                },
            }
            for c in turn.tool_calls
        ]
    return msg


class OpenAICompatLLM:
    def __init__(self, settings: Settings) -> None:
        from openai import AsyncOpenAI  # imported lazily: replay mode never needs it

        self.model = settings.llm_model
        self.client = AsyncOpenAI(
            base_url=settings.llm_base_url,
            api_key=settings.llm_api_key,
            timeout=settings.llm_timeout_s,
            max_retries=1,
        )

    async def next_turn(self, messages, tools, session) -> LLMTurn:
        resp = await self.client.chat.completions.create(
            model=self.model, messages=messages, tools=tools, tool_choice="auto", temperature=0
        )
        return parse_openai_message(resp.choices[0].message)
