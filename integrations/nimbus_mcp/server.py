"""Nimbus MCP: the "fake Gmail" upstream. The synthetic Nimbus Labs World served as MCP tools.

Only reachable through PASSPORT: it refuses to start unless NIMBUS_GATEWAY_KEY (>= 32 chars) is
set, and only the PASSPORT gateway knows that key (it generates one per run and starts this
server as its child). All data is synthetic; nothing leaves the process.

Env:  NIMBUS_GATEWAY_KEY (required), NIMBUS_INBOX (default base; s2_hidden_instruction for the demo)
Logs go to stderr only: on stdio, stdout is the protocol.
"""

from __future__ import annotations

import json
import logging
import os
import sys
from pathlib import Path
from typing import Any

import anyio
import mcp_types as types
from mcp.server import Server

# The backend is imported read-only (World, TOOLS, validate_args, run_tool); nothing in it changes.
BACKEND_DIR = Path(__file__).resolve().parents[2] / "backend"
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from app.tools.registry import TOOLS, InvalidArgs, run_tool, validate_args  # noqa: E402
from app.tools.world import ToolError, World  # noqa: E402

log = logging.getLogger("nimbus_mcp")
MIN_KEY_CHARS = 32
NO_KEY = (
    "nimbus_mcp: this server is only reachable through PASSPORT (NIMBUS_GATEWAY_KEY missing or too short)"
)


def mcp_tools() -> list[types.Tool]:
    tools = []
    for t in TOOLS.values():
        props = {
            p.name: {"type": "integer" if p.type is int else "string", "description": p.description}
            for p in t.params
        }
        schema = {"type": "object", "properties": props, "required": [p.name for p in t.params if p.required]}
        tools.append(types.Tool(name=t.name, description=t.description, input_schema=schema))
    return tools


def _text(text: str, *, error: bool = False) -> types.CallToolResult:
    return types.CallToolResult(content=[types.TextContent(type="text", text=text)], is_error=error)


def build_server(world: World) -> Server:
    async def list_tools(ctx: Any, params: Any) -> types.ListToolsResult:
        return types.ListToolsResult(tools=mcp_tools())

    async def call_tool(ctx: Any, params: types.CallToolRequestParams) -> types.CallToolResult:
        name, args = params.name, params.arguments or {}
        if name not in TOOLS:
            return _text(f"unknown tool {name!r}", error=True)
        try:
            output = run_tool(world, name, validate_args(name, args))
        except (InvalidArgs, ToolError) as e:
            return _text(f"tool error: {e}", error=True)
        log.info("tool=%s ok", name)  # never the args or output: they may hold a secret
        return _text(output if isinstance(output, str) else json.dumps(output, ensure_ascii=False))

    return Server("nimbus-mcp", version="0.1.0", on_list_tools=list_tools, on_call_tool=call_tool)


def key_ok(env: dict[str, str] | os._Environ) -> bool:
    return len(env.get("NIMBUS_GATEWAY_KEY", "")) >= MIN_KEY_CHARS


async def _run_stdio(server: Server) -> None:
    from mcp.server.stdio import stdio_server

    async with stdio_server() as (read, write):
        await server.run(read, write, server.create_initialization_options())


def main() -> None:
    logging.basicConfig(stream=sys.stderr, level=logging.INFO, format="%(asctime)s %(name)s %(message)s")
    if not key_ok(os.environ):
        print(NO_KEY, file=sys.stderr)
        sys.exit(2)
    world = World(inbox=os.environ.get("NIMBUS_INBOX", "base"))
    anyio.run(_run_stdio, build_server(world))


if __name__ == "__main__":
    main()
