"""Gmail MCP: the REAL Gmail connector behind the PASSPORT gateway (architecture box 3, "tool connectors").

It serves the same tool names and parameters PASSPORT already guards (backend/app/tools/registry.py),
so every rule applies unchanged:
  list_unread_emails  your 10 newest unread inbox emails (ids 1..10 for this run)
  read_email          one of those, by id
  send_email          creates a Gmail DRAFT, never sends: you review it and press Send yourself
Only reachable through PASSPORT: it refuses to start without GMAIL_GATEWAY_KEY (32+ chars), which the
gateway generates per run and gives only to this child process. The Google sign-in lives in
~/.passport/gmail-token.json (make gmail-login), outside the repo. Logs: tool name only, to stderr.

Run by the gateway when PASSPORT_UPSTREAM=gmail; never by hand.
"""

from __future__ import annotations

import base64
import html
import json
import logging
import os
import re
import sys
from email.message import EmailMessage
from pathlib import Path
from typing import Any

import anyio
import httpx
import mcp_types as types
from mcp.server import Server

sys.path.insert(0, str(Path(__file__).resolve().parent))
from oauth import AccessToken, AuthError, load_credentials  # noqa: E402

BACKEND_DIR = Path(__file__).resolve().parents[2] / "backend"
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))
from app.tools.registry import TOOLS, InvalidArgs, validate_args  # noqa: E402

log = logging.getLogger("gmail_mcp")
API = "https://gmail.googleapis.com/gmail/v1/users/me"
SERVED = ("list_unread_emails", "read_email", "send_email")
MAX_EMAILS = 10
MAX_BODY = 4000
MIN_KEY_CHARS = 32
NO_KEY = "gmail_mcp: this server is only reachable through PASSPORT (GMAIL_GATEWAY_KEY missing or too short)"
# One plain address, nothing glued on: "a@x.com, b@evil.test" must not slip a second recipient past the trace.
ONE_ADDRESS = re.compile(r"^[A-Za-z0-9._%+\-]+@[A-Za-z0-9\-]+(?:\.[A-Za-z0-9\-]+)+$")


class GmailError(Exception):
    """A Gmail call failed. The message is safe to show the agent (no tokens, no response bodies)."""


def _b64(data: str) -> str:
    return base64.urlsafe_b64decode(data + "=" * (-len(data) % 4)).decode("utf-8", errors="replace")


def html_to_text(s: str) -> str:
    """ALL text of the HTML, including text styled to be invisible (white, 1px, display:none): that is
    exactly where hidden instructions live, and PASSPORT must label what the agent will read."""
    s = re.sub(r"(?is)<(script|style)\b.*?</\1\s*>", " ", s)
    s = re.sub(r"(?i)<br\s*/?>|</(p|div|li|tr|h\d)\s*>", "\n", s)
    s = re.sub(r"(?s)<[^>]+>", " ", s)
    s = html.unescape(s)
    lines = [re.sub(r"[ \t ]+", " ", ln).strip() for ln in s.splitlines()]
    return "\n".join(ln for ln in lines if ln)


def body_text(payload: dict[str, Any]) -> str:
    """Prefer the HTML part (it holds hidden text a plain-text part may drop), else the plain part."""
    found: dict[str, str] = {}

    def walk(p: dict[str, Any]) -> None:
        mime, data = p.get("mimeType", ""), (p.get("body") or {}).get("data")
        if data and mime in ("text/plain", "text/html") and mime not in found:
            found[mime] = _b64(data)
        for part in p.get("parts") or []:
            walk(part)

    walk(payload)
    if "text/html" in found:
        return html_to_text(found["text/html"])[:MAX_BODY]
    return found.get("text/plain", "").strip()[:MAX_BODY]


def header(payload: dict[str, Any], name: str) -> str:
    for h in payload.get("headers") or []:
        if str(h.get("name", "")).lower() == name.lower():
            return str(h.get("value", ""))[:300]
    return ""


class Gmail:
    """The three Gmail REST calls the connector needs (users.messages.list/get, users.drafts.create)."""

    def __init__(self, http: httpx.AsyncClient, token: AccessToken) -> None:
        self.http, self.token = http, token
        self.ids: dict[int, str] = {}  # our small ids (1..10) -> Gmail message ids, for this run

    async def _call(self, method: str, path: str, **kw: Any) -> dict[str, Any]:
        for attempt in (0, 1):
            try:
                token = await self.token.get(force=attempt == 1)
            except AuthError as e:
                raise GmailError(str(e)) from e
            r = await self.http.request(
                method, API + path, headers={"Authorization": f"Bearer {token}"}, timeout=20, **kw
            )
            if r.status_code == 401 and attempt == 0:
                continue  # the access token expired early: refresh once
            if r.status_code >= 400:
                raise GmailError(f"Gmail answered {r.status_code}")
            return r.json()
        raise GmailError("Gmail refused the sign-in")

    async def list_unread(self) -> list[dict[str, Any]]:
        listed = await self._call(
            "GET", "/messages", params={"q": "is:unread in:inbox", "maxResults": MAX_EMAILS}
        )
        self.ids = {}
        out = []
        for n, m in enumerate(listed.get("messages") or [], start=1):
            self.ids[n] = str(m["id"])
            out.append(await self._email(n))
        return out

    async def read(self, n: int) -> dict[str, Any]:
        if n not in self.ids:
            raise GmailError(f"no email with id {n}: call list_unread_emails first")
        return await self._email(n)

    async def _email(self, n: int) -> dict[str, Any]:
        msg = await self._call("GET", f"/messages/{self.ids[n]}", params={"format": "full"})
        p = msg.get("payload") or {}
        return {"id": n, "from": header(p, "From"), "subject": header(p, "Subject"), "body": body_text(p)}

    async def draft(self, to: str, subject: str, body: str) -> None:
        if not ONE_ADDRESS.match(to):
            raise GmailError("'to' must be exactly one plain email address")
        m = EmailMessage()
        try:
            m["To"] = to
            m["Subject"] = subject
        except ValueError as e:  # a line break in a header would let the caller add headers (Bcc...)
            raise GmailError("the subject can't contain line breaks") from e
        m.set_content(body)
        raw = base64.urlsafe_b64encode(m.as_bytes()).decode()
        await self._call("POST", "/drafts", json={"message": {"raw": raw}})


def mcp_tools() -> list[types.Tool]:
    tools = []
    for name in SERVED:
        t = TOOLS[name]
        props = {
            p.name: {"type": "integer" if p.type is int else "string", "description": p.description}
            for p in t.params
        }
        schema = {"type": "object", "properties": props, "required": [p.name for p in t.params if p.required]}
        desc = t.description
        if name == "send_email":
            desc = "Write an email. It is saved as a draft in the user's Gmail; the user sends it."
        tools.append(types.Tool(name=name, description=desc, input_schema=schema))
    return tools


def _text(text: str, *, error: bool = False) -> types.CallToolResult:
    return types.CallToolResult(content=[types.TextContent(type="text", text=text)], is_error=error)


def build_server(gmail: Gmail) -> Server:
    async def list_tools(ctx: Any, params: Any) -> types.ListToolsResult:
        return types.ListToolsResult(tools=mcp_tools())

    async def call_tool(ctx: Any, params: types.CallToolRequestParams) -> types.CallToolResult:
        name = params.name
        if name not in SERVED:
            return _text(f"unknown tool {name!r}", error=True)
        try:
            args = validate_args(name, params.arguments or {})
            if name == "list_unread_emails":
                out: Any = await gmail.list_unread()
            elif name == "read_email":
                out = await gmail.read(int(args["email_id"]))
            else:
                await gmail.draft(args["to"], args["subject"], args["body"])
                out = "Draft saved in Gmail. It was not sent."  # never echo values back
        except (InvalidArgs, GmailError) as e:
            log.info("tool=%s error", name)
            return _text(f"tool error: {e}", error=True)
        except httpx.HTTPError:
            log.info("tool=%s network error", name)
            return _text("tool error: Gmail is unreachable", error=True)
        log.info("tool=%s ok", name)  # never args or output: they are the user's mail
        return _text(out if isinstance(out, str) else json.dumps(out, ensure_ascii=False))

    return Server("gmail-mcp", version="0.1.0", on_list_tools=list_tools, on_call_tool=call_tool)


async def _run() -> None:
    from mcp.server.stdio import stdio_server

    async with httpx.AsyncClient() as http:
        server = build_server(Gmail(http, AccessToken(load_credentials(), http)))
        async with stdio_server() as (read, write):
            await server.run(read, write, server.create_initialization_options())


def main() -> None:
    logging.basicConfig(stream=sys.stderr, level=logging.INFO, format="%(asctime)s %(name)s %(message)s")
    for noisy in ("httpx", "httpx2"):  # their request lines would print Gmail message ids
        logging.getLogger(noisy).setLevel(logging.WARNING)
    if len(os.environ.get("GMAIL_GATEWAY_KEY", "")) < MIN_KEY_CHARS:
        print(NO_KEY, file=sys.stderr)
        sys.exit(2)
    try:
        load_credentials()
    except AuthError as e:
        print(f"gmail_mcp: {e}", file=sys.stderr)
        sys.exit(2)
    anyio.run(_run)


if __name__ == "__main__":
    main()
