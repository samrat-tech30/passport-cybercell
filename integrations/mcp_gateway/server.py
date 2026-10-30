"""PASSPORT MCP gateway: any MCP client gets the PASSPORT checks before a tool runs.

The gateway serves the simulated Nimbus Labs World (synthetic data only) as MCP tools. Before
every call it asks the backend's `POST /v1/decide`, sending the user's request and every earlier
tool output of this session as labelled context. Anything other than a clear ALLOW is refused,
and so is every error on the way (fail closed).

Run:  python integrations/mcp_gateway/server.py            (stdio, for Claude Desktop)
      python integrations/mcp_gateway/server.py --http --port 8765   (MCP Inspector)
Env:  PASSPORT_URL (default http://127.0.0.1:8000), PASSPORT_INBOX (default base),
      PASSPORT_DEMO_CODE (sent as X-Demo-Code when set)

Logs go to stderr only: on stdio, stdout is the protocol.
"""

from __future__ import annotations

import argparse
import json
import logging
import os
import sys
from pathlib import Path
from typing import Any

import anyio
import httpx
import mcp_types as types
from mcp.server import Server

# The backend is imported read-only (World, TOOLS, validate_args, run_tool); nothing in it changes.
BACKEND_DIR = Path(__file__).resolve().parents[2] / "backend"
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from app.tools.registry import TOOLS, InvalidArgs, run_tool, validate_args  # noqa: E402
from app.tools.world import ToolError, World  # noqa: E402

log = logging.getLogger("passport.mcp_gateway")

# /v1/decide limits (backend/app/api/schemas.py)
MAX_CONTEXT_ITEMS = 50
MAX_CONTEXT_CHARS = 20_000
MAX_SOURCE_CHARS = 200
MAX_REQUEST_CHARS = 2000
DECIDE_TIMEOUT_S = 5.0

UNREACHABLE = "PASSPORT unreachable, failing closed"

START_TASK = types.Tool(
    name="start_task",
    description=(
        "Call this first, once, with the user's request in their own words. "
        "PASSPORT locks it as the intent of this session; other tools are refused until then."
    ),
    inputSchema={
        "type": "object",
        "properties": {"request": {"type": "string", "description": "The user's request, verbatim"}},
        "required": ["request"],
    },
)


def _mcp_tools() -> list[types.Tool]:
    tools = [START_TASK]
    for t in TOOLS.values():
        props = {
            p.name: {"type": "integer" if p.type is int else "string", "description": p.description}
            for p in t.params
        }
        schema = {"type": "object", "properties": props, "required": [p.name for p in t.params if p.required]}
        tools.append(types.Tool(name=t.name, description=t.description, inputSchema=schema))
    return tools


def _text(text: str, *, error: bool = False) -> types.CallToolResult:
    return types.CallToolResult(content=[types.TextContent(type="text", text=text)], isError=error)


class Gateway:
    """State of one gateway process: one World, one intent, one history of tool outputs."""

    def __init__(
        self,
        inbox: str = "base",
        passport_url: str = "http://127.0.0.1:8000",
        demo_code: str | None = None,
        transport: httpx.AsyncBaseTransport | None = None,  # tests: the backend app over ASGI
    ) -> None:
        self.world = World(inbox=inbox)
        self.passport_url = passport_url.rstrip("/")
        self.demo_code = demo_code
        self.transport = transport
        self.user_request: str | None = None
        self.context: list[dict[str, str]] = []  # every earlier tool output, oldest first
        self.calls = 0
        self.lock = anyio.Lock()  # one call at a time, so each decision sees all earlier outputs

    # ---------- MCP handlers ----------
    async def list_tools(self, ctx: Any, params: Any) -> types.ListToolsResult:
        return types.ListToolsResult(tools=_mcp_tools())

    async def call_tool(self, ctx: Any, params: types.CallToolRequestParams) -> types.CallToolResult:
        async with self.lock:
            try:
                return await self._call(params.name, params.arguments or {})
            except Exception:  # never raise: the client would get a bare "Internal server error"
                log.exception("gateway error on %s", params.name)
                return self._refuse(params.name, "ERROR", "gateway error; refused (fail closed)")

    # ---------- the checks ----------
    async def _call(self, name: str, args: dict[str, Any]) -> types.CallToolResult:
        if name == "start_task":
            return self._start_task(args)
        if name not in TOOLS:
            return self._refuse(name, "INVALID", f"unknown tool {name!r}")
        if self.user_request is None:
            return self._refuse(name, "NO_INTENT", "call start_task with the user's request first; refused")
        try:
            clean = validate_args(name, args)
        except InvalidArgs as e:
            return self._refuse(name, "INVALID", f"invalid arguments: {e}; refused")

        decision = await self._decide(name, clean)
        if decision is None:
            return self._refuse(name, "UNREACHABLE", UNREACHABLE)
        verdict, rule_id = decision.get("verdict"), decision.get("rule_id", "?")
        if verdict == "DENY":
            return self._refuse(name, f"DENY {rule_id}", _deny_text(decision))
        if verdict == "REQUIRE_APPROVAL":
            reason = decision.get("message", "")
            return self._refuse(
                name,
                f"REQUIRE_APPROVAL {rule_id}",
                f"PASSPORT REQUIRE_APPROVAL {rule_id}: {reason}\nneeds human approval; refused (fail closed)",
            )
        if verdict != "ALLOW":
            return self._refuse(name, "UNREACHABLE", UNREACHABLE)

        try:
            output = run_tool(self.world, name, clean)
        except ToolError as e:
            log.info("tool=%s verdict=ALLOW rule=%s tool_error", name, rule_id)
            return _text(f"tool error: {e}", error=True)
        self.calls += 1
        self._remember(name, output)
        log.info("tool=%s verdict=ALLOW rule=%s", name, rule_id)
        return _text(output if isinstance(output, str) else json.dumps(output, ensure_ascii=False, indent=2))

    def _start_task(self, args: dict[str, Any]) -> types.CallToolResult:
        request = args.get("request")
        if self.user_request is not None:
            return self._refuse("start_task", "LOCKED", "intent is locked for this session; refused")
        if set(args) != {"request"} or not isinstance(request, str) or not request.strip():
            return self._refuse("start_task", "INVALID", "start_task needs one text argument: request")
        if len(request) > MAX_REQUEST_CHARS:
            return self._refuse(
                "start_task", "INVALID", f"request is longer than {MAX_REQUEST_CHARS} characters"
            )
        self.user_request = request.strip()
        log.info("tool=start_task verdict=LOCKED")
        return _text("Intent locked. PASSPORT will check every tool call against this request.")

    async def _decide(self, tool: str, args: dict[str, Any]) -> dict[str, Any] | None:
        """Ask the backend. None means no usable answer: the caller fails closed."""
        body = {
            "tool": tool,
            "args": args,
            "user_request": self.user_request,
            "context": self.context[-MAX_CONTEXT_ITEMS:],  # keep the newest
        }
        headers = {"X-Demo-Code": self.demo_code} if self.demo_code else {}
        try:
            async with httpx.AsyncClient(
                base_url=self.passport_url, transport=self.transport, timeout=DECIDE_TIMEOUT_S
            ) as http:
                r = await http.post("/v1/decide", json=body, headers=headers)
            if r.status_code != 200:
                log.warning("decide returned HTTP %s", r.status_code)
                return None
            data = r.json()
        except (httpx.HTTPError, ValueError) as e:
            log.warning("decide failed: %s", type(e).__name__)
            return None
        return data if isinstance(data, dict) else None

    def _remember(self, tool: str, output: Any) -> None:
        """Label the output for later decisions with the tool's trust (untrusted / trusted / secret)."""
        trust = TOOLS[tool].output_trust.value
        source = f"{tool} #{self.calls}"
        emails = output if tool == "list_unread_emails" else [output] if tool == "read_email" else None
        if emails is not None:  # one item per email, so evidence points at a line of that email
            for e in emails:
                text = f"From: {e['from']}\nSubject: {e['subject']}\n\n{e['body']}"
                self._add(f"{source}, email #{e['id']} from {e['from']}", trust, text)
        else:
            self._add(
                source, trust, output if isinstance(output, str) else json.dumps(output, ensure_ascii=False)
            )

    def _add(self, source: str, trust: str, text: str) -> None:
        self.context.append(
            {"source": source[:MAX_SOURCE_CHARS], "trust": trust, "text": text[:MAX_CONTEXT_CHARS]}
        )
        del self.context[:-MAX_CONTEXT_ITEMS]

    def _refuse(self, tool: str, verdict: str, message: str) -> types.CallToolResult:
        log.info("tool=%s verdict=%s", tool, verdict)  # never the args: they may hold a secret
        return _text(message, error=True)


def _deny_text(d: dict[str, Any]) -> str:
    lines = [f"PASSPORT DENY {d.get('rule_id', '?')}: {d.get('message', '')}"]
    for p in d.get("passports") or []:
        if p.get("origin") in ("untrusted", "secret") or p.get("line"):
            where = p.get("source") or p.get("segment_id") or "?"
            if p.get("line"):
                where += f", line {p['line']}"
            snippet = f": {p['snippet']}" if p.get("snippet") else ""
            lines.append(f"- {p.get('arg')} = {p.get('value')!r} came from {where}{snippet}")
    return "\n".join(lines)


def build_server(gateway: Gateway) -> Server:
    return Server(
        "passport-gateway",
        version="0.1.0",
        instructions="Call start_task first with the user's request. PASSPORT checks every other tool call.",
        on_list_tools=gateway.list_tools,
        on_call_tool=gateway.call_tool,
    )


def gateway_from_env() -> Gateway:
    return Gateway(
        inbox=os.environ.get("PASSPORT_INBOX", "base"),
        passport_url=os.environ.get("PASSPORT_URL", "http://127.0.0.1:8000"),
        demo_code=os.environ.get("PASSPORT_DEMO_CODE") or None,
    )


async def _run_stdio(server: Server) -> None:
    from mcp.server.stdio import stdio_server

    async with stdio_server() as (read, write):
        await server.run(read, write, server.create_initialization_options())


def main() -> None:
    parser = argparse.ArgumentParser(description="PASSPORT MCP gateway")
    parser.add_argument("--http", action="store_true", help="serve streamable HTTP instead of stdio")
    parser.add_argument("--port", type=int, default=8765)
    a = parser.parse_args()
    logging.basicConfig(stream=sys.stderr, level=logging.INFO, format="%(asctime)s %(name)s %(message)s")

    gateway = gateway_from_env()
    server = build_server(gateway)
    log.info(
        "PASSPORT gateway: backend %s, inbox %s",
        gateway.passport_url,
        os.environ.get("PASSPORT_INBOX", "base"),
    )
    if a.http:
        import uvicorn

        uvicorn.run(server.streamable_http_app(host="127.0.0.1"), host="127.0.0.1", port=a.port)
    else:
        anyio.run(_run_stdio, server)


if __name__ == "__main__":
    main()
