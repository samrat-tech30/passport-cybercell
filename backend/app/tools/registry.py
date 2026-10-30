"""The tool catalogue: what each tool does, its parameters, and how its output is labelled.

Tool functions are never handed to the LLM directly. Only app.gate.handle.execute() may call
them, and only after the gate has decided.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from app.contracts import Trust
from app.tools.world import ToolError, World


@dataclass(frozen=True)
class Param:
    name: str
    type: type  # str or int
    description: str
    required: bool = True


@dataclass(frozen=True)
class ToolSpec:
    name: str
    description: str
    params: tuple[Param, ...]
    output_trust: Trust  # label for whatever the tool returns


TOOLS: dict[str, ToolSpec] = {
    t.name: t
    for t in [
        ToolSpec(
            "list_unread_emails",
            "List the user's unread emails with sender, subject and body.",
            (),
            Trust.UNTRUSTED,
        ),
        ToolSpec(
            "read_email",
            "Read one email by its id.",
            (Param("email_id", int, "The email id"),),
            Trust.UNTRUSTED,
        ),
        ToolSpec(
            "send_email",
            "Send an email.",
            (
                Param("to", str, "Recipient email address"),
                Param("subject", str, "Subject line"),
                Param("body", str, "Email body"),
            ),
            Trust.TRUSTED,
        ),
        ToolSpec(
            "read_file",
            "Read a file from the shared drive.",
            (Param("path", str, "Path inside the shared drive"),),
            Trust.UNTRUSTED,
        ),
        ToolSpec(
            "read_secret",
            "Read a secret value from the company vault.",
            (Param("key", str, "Secret name"),),
            Trust.SECRET,
        ),
        ToolSpec(
            "pay_invoice",
            "Pay a vendor invoice.",
            (
                Param("account", str, "Bank account to pay"),
                Param("amount_inr", int, "Amount in rupees"),
                Param("memo", str, "Payment memo", required=False),
            ),
            Trust.TRUSTED,
        ),
        ToolSpec(
            "delete_file",
            "Delete a file from the shared drive.",
            (Param("path", str, "Path inside the shared drive"),),
            Trust.TRUSTED,
        ),
    ]
}


def openai_tool_schemas() -> list[dict[str, Any]]:
    """Tool definitions in the OpenAI-compatible function-calling format."""
    out = []
    for t in TOOLS.values():
        props = {
            p.name: {"type": "integer" if p.type is int else "string", "description": p.description}
            for p in t.params
        }
        out.append(
            {
                "type": "function",
                "function": {
                    "name": t.name,
                    "description": t.description,
                    "parameters": {
                        "type": "object",
                        "properties": props,
                        "required": [p.name for p in t.params if p.required],
                    },
                },
            }
        )
    return out


class InvalidArgs(ValueError):
    pass


def validate_args(tool: str, args: Any) -> dict[str, Any]:
    """Check names and types strictly. Anything odd is rejected (the gate then fails closed)."""
    spec = TOOLS.get(tool)
    if spec is None:
        raise InvalidArgs(f"unknown tool {tool!r}")
    if not isinstance(args, dict):
        raise InvalidArgs("arguments must be an object")
    allowed = {p.name: p for p in spec.params}
    extra = set(args) - set(allowed)
    if extra:
        raise InvalidArgs(f"unexpected argument(s): {', '.join(sorted(extra))}")
    clean: dict[str, Any] = {}
    for p in spec.params:
        if p.name not in args:
            if p.required:
                raise InvalidArgs(f"missing argument: {p.name}")
            continue
        v = args[p.name]
        if p.type is int:
            if isinstance(v, bool):
                raise InvalidArgs(f"{p.name} must be a whole number")
            if isinstance(v, str) and v.replace(",", "").strip().isdigit():
                v = int(v.replace(",", "").strip())
            if not isinstance(v, int):
                raise InvalidArgs(f"{p.name} must be a whole number")
        else:
            if not isinstance(v, str):
                raise InvalidArgs(f"{p.name} must be text")
            if len(v) > 10_000:
                raise InvalidArgs(f"{p.name} is too long")
        clean[p.name] = v
    return clean


def run_tool(world: World, tool: str, args: dict[str, Any]) -> Any:
    fn = getattr(world, tool, None)
    if fn is None or tool not in TOOLS:
        raise ToolError(f"unknown tool {tool!r}")
    return fn(**args)
