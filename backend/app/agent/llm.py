"""LLM back-ends behind one tiny interface: next_turn(messages, tools, session) -> LLMTurn.

* ReplayLLM: returns a recorded/scripted plan of tool calls (from the scenario YAML). Used for the
  stage demo, the eval and tests: no network, same result every time. The GATE still runs live.
* OpenAICompatLLM: any OpenAI-compatible chat API (Groq, OpenRouter, Ollama, OpenAI...).
"""

from __future__ import annotations

import asyncio
import base64
import json
import re
import urllib.parse
from collections.abc import Callable
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any, Protocol

from app.config import Settings

if TYPE_CHECKING:
    from app.sessions import Session

# {{secret:NAME}} or {{secret:NAME:b64}}: same encodings as World.secret_forms(), so a recorded
# live run that leaked a base64 secret replays as the same base64 leak.
_SECRET_TMPL = re.compile(r"\{\{secret:([A-Z0-9_]+)(?::([a-z0-9]+))?\}\}")
SECRET_ENCODINGS: dict[str, Callable[[str], str]] = {
    "raw": lambda v: v,
    "b64": lambda v: base64.b64encode(v.encode()).decode(),
    "b64url": lambda v: base64.urlsafe_b64encode(v.encode()).decode(),
    "hex": lambda v: v.encode().hex(),
    "url": lambda v: urllib.parse.quote(v, safe=""),
    "rev": lambda v: v[::-1],
}


class LLMError(RuntimeError):
    """A live-LLM failure whose message is safe to show in the UI (no key, no stack trace)."""


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
                name, enc = m.group(1), m.group(2) or "raw"
                if name not in session.gate.store.revealed or enc not in SECRET_ENCODINGS:
                    return "[unknown]"
                return SECRET_ENCODINGS[enc](session.world.vault[name])

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


def _retry_after_s(err: Any, cap: float = 5.0) -> float:
    try:
        return min(max(float(err.response.headers.get("retry-after", "2")), 0.0), cap)
    except (AttributeError, TypeError, ValueError):
        return 2.0


class OpenAICompatLLM:
    """Retries are ours, not the SDK's: a 429 gets exactly one retry, a timeout none (a retried
    timeout doubles the wait on stage). Every failure becomes an LLMError with a readable message."""

    def __init__(self, settings: Settings, client: Any = None) -> None:
        self.model = settings.llm_model
        self.timeout_s = settings.llm_timeout_s
        self.hard_timeout_s: float = settings.llm_timeout_s + 5  # backstop if the client itself hangs
        if client is None:
            from openai import AsyncOpenAI  # imported lazily: replay mode never needs it

            client = AsyncOpenAI(
                base_url=settings.llm_base_url,
                api_key=settings.llm_api_key,
                timeout=settings.llm_timeout_s,
                max_retries=0,
            )
        self.client = client

    async def next_turn(self, messages, tools, session) -> LLMTurn:
        import openai

        for attempt in (1, 2):
            try:
                resp = await asyncio.wait_for(
                    self.client.chat.completions.create(
                        model=self.model, messages=messages, tools=tools, tool_choice="auto", temperature=0
                    ),
                    timeout=self.hard_timeout_s,
                )
                return parse_openai_message(resp.choices[0].message)
            except (openai.APITimeoutError, TimeoutError) as e:
                raise LLMError(f"The LLM did not answer within {self.timeout_s} s.") from e
            except openai.RateLimitError as e:
                if attempt == 2:
                    raise LLMError("The LLM provider is rate-limiting us (HTTP 429). Use replay mode.") from e
                await asyncio.sleep(_retry_after_s(e))
            except openai.APIStatusError as e:
                raise LLMError(f"The LLM provider returned HTTP {e.status_code}.") from e
            except openai.APIConnectionError as e:
                raise LLMError("Could not reach the LLM provider.") from e
        raise LLMError("The LLM gave no answer.")  # unreachable: the loop returns or raises
