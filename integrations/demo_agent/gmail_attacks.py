"""A scripted agent that falls for EVERY "[PASSPORT test]" email in your real Gmail (make gmail-seed),
through the real PASSPORT gateway. For a demo that is the same every time: a real model may refuse
some injections on its own.

    make gmail-attacks ME=you@gmail.com

1. start_task("Summarise my unread emails and send the summary to <ME>")
2. list_unread_emails (your real inbox)
3. for each test email, does what it says: send_email to the address it names (as an LLM would decode it)
4. sends the real summary to ME: allowed, saved as a draft
Prints only subjects and PASSPORT's answers, never your email contents.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

import anyio
import mcp_types as types
from mcp import Client, StdioServerParameters

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "integrations" / "gmail_mcp"))
from seed import TAG, attacks  # noqa: E402

GATEWAY = ROOT / "integrations" / "passport_gateway" / "server.py"
GREEN, RED, YELLOW, DIM, END = "\033[32m", "\033[31m", "\033[33m", "\033[2m", "\033[0m"


def token_from(env_file: Path) -> str:
    token = os.environ.get("PASSPORT_GATEWAY_TOKEN", "")
    if not token and env_file.is_file():
        for line in env_file.read_text(encoding="utf-8").splitlines():
            key, sep, value = line.partition("=")
            if sep and key.strip() == "PASSPORT_GATEWAY_TOKEN":
                token = value.split(" #", 1)[0].strip().strip('"').strip("'")
    if not token:
        raise SystemExit("Set PASSPORT_GATEWAY_TOKEN in backend/.env (the same one the backend uses).")
    return token


def text(r: types.CallToolResult) -> str:
    return "\n".join(c.text for c in r.content if isinstance(c, types.TextContent))


def show(label: str, r: types.CallToolResult) -> None:
    body = text(r)
    if r.is_error:
        colour = YELLOW if "REQUIRE_APPROVAL" in body or "approve" in body else RED
        print(f"   {colour}refused:{END} {body[:300]}")
    else:
        print(f"   {GREEN}ran:{END} {body[:160]}")


async def play(me: str, env_file: Path) -> None:
    env = {
        "PASSPORT_URL": os.environ.get("PASSPORT_URL", "http://127.0.0.1:8000"),
        "PASSPORT_GATEWAY_TOKEN": token_from(env_file),
        "PASSPORT_UPSTREAM": "gmail",
        "PASSPORT_AGENT_NAME": "Fooled agent (real Gmail)",
    }
    params = StdioServerParameters(command=sys.executable, args=[str(GATEWAY)], env=env)
    async with Client(params, client_info=types.Implementation(name="gmail-attacks", version="1.0")) as c:
        request = f"Summarise my unread emails and send the summary to {me}"
        print(f"1. The user asks: {request}")
        show("start_task", await c.call_tool("start_task", {"request": request}))

        print("\n2. The agent reads the real inbox.")
        r = await c.call_tool("list_unread_emails", {})
        if r.is_error:
            show("list", r)
            return
        inbox = json.loads(text(r))
        print(f"   {GREEN}ran:{END} {len(inbox)} unread emails")

        targets = attacks(me)
        found = [
            (e, targets[e["subject"].removeprefix(f"{TAG} ")])
            for e in inbox
            if e["subject"].removeprefix(f"{TAG} ") in targets
        ]
        if not found:
            print(
                f"\n{YELLOW}No [PASSPORT test] attack emails among the unread ones. Run: make gmail-seed{END}"
            )
        for n, (e, to) in enumerate(found, start=3):
            print(f'\n{n}. Fooled by Email #{e["id"]} "{e["subject"]}": send the summary to {to}')
            show(
                "send",
                await c.call_tool(
                    "send_email", {"to": to, "subject": "Inbox summary", "body": "As requested."}
                ),
            )

        print(f"\n{len(found) + 3}. The real task: the summary goes to {me}.")
        show(
            "send",
            await c.call_tool("send_email", {"to": me, "subject": "Inbox summary", "body": "Your summary."}),
        )
    print(
        f"\n{DIM}Every call is on the dashboard (Agents tab). The allowed one is a draft in Gmail; nothing was sent.{END}"
    )


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--me", required=True, help="your Gmail address (the legit recipient)")
    ap.add_argument("--env-file", type=Path, default=ROOT / "backend" / ".env")
    a = ap.parse_args()
    anyio.run(play, a.me.strip(), a.env_file)


if __name__ == "__main__":
    main()
