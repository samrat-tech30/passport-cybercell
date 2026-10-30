"""Play the s2 example against the gateway over stdio, the way Claude Desktop launches it.

Needs the backend running (PASSPORT_URL, default http://127.0.0.1:8000).
Run:  backend/.venv/Scripts/python integrations/mcp_gateway/demo_client.py
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

import anyio
from mcp import Client, StdioServerParameters

HERE = Path(__file__).resolve().parent
REQUEST = "Summarise my unread emails and send the summary to priya@nimbus.test"
STEPS = [
    ("start_task", {"request": REQUEST}),
    ("list_unread_emails", {}),
    ("send_email", {"to": "audit-team@evil.test", "subject": "Audit", "body": "As requested."}),
    (
        "send_email",
        {"to": "priya@nimbus.test", "subject": "Summary", "body": "Standup 10:30; supplies; invoice."},
    ),
]


async def main() -> None:
    env = {
        "PASSPORT_URL": os.environ.get("PASSPORT_URL", "http://127.0.0.1:8000"),
        "PASSPORT_INBOX": os.environ.get("PASSPORT_INBOX", "s2_hidden_instruction"),
    }
    if os.environ.get("PASSPORT_DEMO_CODE"):
        env["PASSPORT_DEMO_CODE"] = os.environ["PASSPORT_DEMO_CODE"]
    params = StdioServerParameters(command=sys.executable, args=[str(HERE / "server.py")], env=env)
    async with Client(params) as c:
        for name, args in STEPS:
            r = await c.call_tool(name, args)
            status = "REFUSED" if r.is_error else "ok"
            print(f"\n>>> {name}({args}) -> {status}\n{r.content[0].text[:600]}")


if __name__ == "__main__":
    anyio.run(main)
