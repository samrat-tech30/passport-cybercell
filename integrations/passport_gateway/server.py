"""PASSPORT gateway: an MCP server for the agent, an MCP client to the upstream (Nimbus) server.

    agent (Claude Desktop, fooled_agent.py) --MCP stdio--> this gateway --HTTP /v1/gateway/*--> backend
                                                           this gateway --MCP stdio--> nimbus_mcp (child)

Every call: POST /decide → run upstream ONLY if run=true → POST /observe with the output → return
it. Anything unclear on the way (backend down, non-2xx, odd JSON, unknown tool, upstream error,
observe refused) is a refusal: fail closed. The upstream key is random per run and lives only in
the child's environment, so the agent's config holds no upstream credential.

Run:  python integrations/passport_gateway/server.py            (stdio, for Claude Desktop)
      python integrations/passport_gateway/server.py --http --port 8765   (MCP Inspector)
Env:  PASSPORT_URL (default http://127.0.0.1:8000), PASSPORT_GATEWAY_TOKEN (required),
      PASSPORT_SHIELD (on|off, default on), PASSPORT_AGENT_NAME (default "Claude Desktop"),
      NIMBUS_INBOX (default base)
Logs go to stderr only (one line per call: tool, verdict, rule, run); never tokens or outputs.
"""

from __future__ import annotations

import argparse
import logging
import os
import secrets
import sys
from pathlib import Path
from typing import Any

import anyio
import httpx
import mcp_types as types
from mcp import Client, StdioServerParameters
from mcp.server import Server

log = logging.getLogger("passport.gateway")

NIMBUS_SERVER = Path(__file__).resolve().parents[1] / "nimbus_mcp" / "server.py"
FAIL_CLOSED = "PASSPORT unreachable or refused, failing closed"
HTTP_TIMEOUT_S = 10.0

START_TASK = types.Tool(
    name="start_task",
    description=(
        "Call this FIRST with the user's exact request, before any other tool. "
        "PASSPORT locks it as the intent of this session and checks every later tool call against it."
    ),
    input_schema={
        "type": "object",
        "properties": {"request": {"type": "string", "description": "The user's request, verbatim"}},
        "required": ["request"],
    },
)


def _text(text: str, *, error: bool = False) -> types.CallToolResult:
    return types.CallToolResult(content=[types.TextContent(type="text", text=text)], is_error=error)


class Refused(Exception):
    """A reason to refuse the call; the message goes to the agent."""


class Gateway:
    """One gateway process = one PASSPORT session = one upstream."""

    def __init__(
        self,
        upstream: Any,  # an initialised mcp Client (stdio child in production, in-memory in tests)
        upstream_tools: list[types.Tool],
        *,
        passport_url: str = "http://127.0.0.1:8000",
        token: str = "",
        shield_on: bool = True,
        agent_name: str = "Claude Desktop",
        approval_wait_s: int = 40,
        transport: httpx.AsyncBaseTransport | None = None,  # tests: the backend app over ASGI
    ) -> None:
        self.upstream = upstream
        self.upstream_tools = {t.name: t for t in upstream_tools if t.name != START_TASK.name}
        self.passport_url = passport_url.rstrip("/")
        self.token = token
        self.shield_on = shield_on
        self.agent_name = agent_name
        self.decide_timeout_s = approval_wait_s + 10  # the backend may hold /decide for an approval
        self.transport = transport
        self.session_id: str | None = None
        self.lock = anyio.Lock()  # one call at a time: each decision sees every earlier output

    # ---------- MCP handlers ----------
    async def list_tools(self, ctx: Any, params: Any) -> types.ListToolsResult:
        return types.ListToolsResult(tools=[START_TASK, *self.upstream_tools.values()])

    async def call_tool(self, ctx: Any, params: types.CallToolRequestParams) -> types.CallToolResult:
        name, args = params.name, params.arguments or {}
        async with self.lock:
            try:
                return await self._call(ctx, name, args)
            except Refused as e:
                return _text(str(e), error=True)
            except Exception:  # never raise: the client would get a bare "Internal server error"
                log.exception("gateway error on %s", name)
                log.info("tool=%s verdict=ERROR run=False", name)
                return _text(FAIL_CLOSED, error=True)

    # ---------- the flow ----------
    async def _call(self, ctx: Any, name: str, args: dict[str, Any]) -> types.CallToolResult:
        if name == START_TASK.name:
            return await self._start_task(ctx, args)
        if name not in self.upstream_tools:
            log.info("tool=%s verdict=UNKNOWN_TOOL run=False", name[:64])
            raise Refused(f"PASSPORT refused: unknown tool {name[:64]!r}")
        sid = await self._session(ctx)
        status, body = await self._post(
            f"/v1/gateway/sessions/{sid}/decide", {"tool": name, "args": args}, self.decide_timeout_s
        )
        if status == 409 and _code(body) == "intent_required":
            log.info("tool=%s verdict=NO_INTENT run=False", name)
            raise Refused("PASSPORT refused: call start_task with the user's request first")
        if status != 200 or not _decide_shape(body):
            log.info("tool=%s verdict=UNREADABLE run=False", name)
            raise Refused(FAIL_CLOSED)
        d, run = body["decision"], body["run"]
        log.info("tool=%s verdict=%s rule=%s run=%s", name, d["verdict"], d["rule_id"], run)
        if not run:
            raise Refused(_refusal_text(body))

        result = await self.upstream.call_tool(name, args)
        output = "\n".join(c.text for c in result.content if getattr(c, "type", "") == "text")
        if result.is_error:
            log.info("tool=%s upstream_error", name)
            raise Refused(f"PASSPORT: the tool failed upstream, nothing returned ({FAIL_CLOSED})")
        status, _ = await self._post(
            f"/v1/gateway/sessions/{sid}/observe", {"decision_id": d["id"], "output": output}, HTTP_TIMEOUT_S
        )
        if status != 200:  # PASSPORT must label the output before the agent may see it
            log.info("tool=%s observe_failed status=%s", name, status)
            raise Refused(FAIL_CLOSED)
        if d["verdict"] != "ALLOW":  # monitor mode: say what PASSPORT would have done
            return _text(f"[{body['message']}]\n{output}")
        return _text(output)

    async def _start_task(self, ctx: Any, args: dict[str, Any]) -> types.CallToolResult:
        request = args.get("request")
        if set(args) != {"request"} or not isinstance(request, str) or not request.strip():
            raise Refused("PASSPORT refused: start_task needs one text argument, request")
        sid = await self._session(ctx)
        status, body = await self._post(
            f"/v1/gateway/sessions/{sid}/intent", {"request": request}, HTTP_TIMEOUT_S
        )
        if status == 409 and _code(body) == "intent_locked":
            log.info("tool=start_task verdict=LOCKED run=False")
            raise Refused("PASSPORT refused: intent is locked for this session")
        if status != 200 or not isinstance(body, dict) or not isinstance(body.get("capsule"), dict):
            log.info("tool=start_task verdict=UNREADABLE run=False")
            raise Refused(FAIL_CLOSED)
        log.info("tool=start_task verdict=INTENT_SET")
        summary = body["capsule"].get("summary", "")
        return _text(f"Intent locked. PASSPORT will check every tool call against it. {summary}".strip())

    async def _session(self, ctx: Any) -> str:
        """Create the PASSPORT session on the first call (the client's name is known by then)."""
        if self.session_id is not None:
            return self.session_id
        body = {
            "agent_name": self.agent_name[:60],
            "client": _client_name(ctx)[:60],
            "shield_on": self.shield_on,
        }
        status, data = await self._post("/v1/gateway/sessions", body, HTTP_TIMEOUT_S)
        if status != 201 or not isinstance(data, dict) or not isinstance(data.get("session_id"), str):
            log.info("create_session failed status=%s", status)
            raise Refused(FAIL_CLOSED)
        self.session_id = data["session_id"]
        log.info("PASSPORT session %s (shield %s)", self.session_id, "on" if self.shield_on else "off")
        return self.session_id

    async def _post(self, path: str, body: dict[str, Any], timeout: float) -> tuple[int, Any]:
        """(status, parsed JSON or None). Status 0 = no answer at all."""
        try:
            async with httpx.AsyncClient(
                base_url=self.passport_url, transport=self.transport, timeout=timeout
            ) as http:
                r = await http.post(path, json=body, headers={"X-Gateway-Token": self.token})
        except httpx.HTTPError as e:
            log.warning("PASSPORT request failed: %s", type(e).__name__)
            return 0, None
        try:
            return r.status_code, r.json()
        except ValueError:
            return r.status_code, None


def _code(body: Any) -> str | None:
    err = body.get("error") if isinstance(body, dict) else None
    return err.get("code") if isinstance(err, dict) else None


def _decide_shape(body: Any) -> bool:
    if (
        not isinstance(body, dict)
        or not isinstance(body.get("run"), bool)
        or not isinstance(body.get("message"), str)
    ):
        return False
    d = body.get("decision")
    return (
        isinstance(d, dict)
        and isinstance(d.get("id"), str)
        and d.get("verdict") in ("ALLOW", "REQUIRE_APPROVAL", "DENY")
        and isinstance(d.get("rule_id"), str)
    )


def _refusal_text(body: dict[str, Any]) -> str:
    lines = [body["message"]]
    for p in body["decision"].get("passports") or []:
        if isinstance(p, dict) and (p.get("origin") in ("untrusted", "secret") or p.get("line")):
            where = p.get("source") or p.get("segment_id") or "?"
            if p.get("line"):
                where += f", line {p['line']}"
            snippet = f": {p['snippet']}" if p.get("snippet") else ""
            lines.append(f"- {p.get('arg')} = {p.get('value')!r} came from {where}{snippet}")
    lines.append("The tool was not called.")
    return "\n".join(lines)


def _client_name(ctx: Any) -> str:
    try:
        return ctx.session.client_params.client_info.name or "unknown"
    except AttributeError:
        return "unknown"


def build_server(gateway: Gateway) -> Server:
    return Server(
        "passport-gateway",
        version="0.2.0",
        instructions="Call start_task first with the user's exact request. PASSPORT checks every other tool call.",
        on_list_tools=gateway.list_tools,
        on_call_tool=gateway.call_tool,
    )


def nimbus_params(inbox: str) -> StdioServerParameters:
    """The upstream as a child process. Its key exists only in its own environment."""
    env = {"NIMBUS_GATEWAY_KEY": secrets.token_hex(32), "NIMBUS_INBOX": inbox}
    return StdioServerParameters(command=sys.executable, args=[str(NIMBUS_SERVER)], env=env)


async def serve(http_port: int | None) -> None:
    token = os.environ.get("PASSPORT_GATEWAY_TOKEN", "")
    if not token:
        log.error("PASSPORT_GATEWAY_TOKEN is not set; refusing to start")
        sys.exit(2)
    shield = os.environ.get("PASSPORT_SHIELD", "on").strip().lower()
    if shield not in ("on", "off"):
        log.error("PASSPORT_SHIELD must be on or off")
        sys.exit(2)
    inbox = os.environ.get("NIMBUS_INBOX", "base")
    async with Client(nimbus_params(inbox)) as upstream:
        tools = (await upstream.list_tools()).tools
        gateway = Gateway(
            upstream,
            tools,
            passport_url=os.environ.get("PASSPORT_URL", "http://127.0.0.1:8000"),
            token=token,
            shield_on=shield == "on",
            agent_name=os.environ.get("PASSPORT_AGENT_NAME", "Claude Desktop"),
            approval_wait_s=int(os.environ.get("GATEWAY_APPROVAL_WAIT_S", "40")),
        )
        server = build_server(gateway)
        log.info(
            "PASSPORT gateway: backend %s, shield %s, %d upstream tools",
            gateway.passport_url,
            shield,
            len(tools),
        )
        if http_port is None:
            from mcp.server.stdio import stdio_server

            async with stdio_server() as (read, write):
                await server.run(read, write, server.create_initialization_options())
        else:
            import uvicorn

            config = uvicorn.Config(
                server.streamable_http_app(host="127.0.0.1"), host="127.0.0.1", port=http_port
            )
            await uvicorn.Server(config).serve()


def main() -> None:
    parser = argparse.ArgumentParser(description="PASSPORT MCP gateway")
    parser.add_argument("--http", action="store_true", help="serve streamable HTTP instead of stdio")
    parser.add_argument("--port", type=int, default=8765)
    a = parser.parse_args()
    logging.basicConfig(stream=sys.stderr, level=logging.INFO, format="%(asctime)s %(name)s %(message)s")
    for name in ("httpx", "httpx2"):  # their request lines would print session URLs
        logging.getLogger(name).setLevel(logging.WARNING)
    anyio.run(serve, a.port if a.http else None)


if __name__ == "__main__":
    main()
