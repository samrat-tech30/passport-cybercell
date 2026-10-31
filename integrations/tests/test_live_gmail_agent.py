"""The live-LLM agent loop (integrations/demo_agent/live_gmail_agent.py) with a FAKE LLM that obeys a
seeded attack email, against the in-process gateway + fake Google: no network, no real account."""

from __future__ import annotations

import json

import httpx
import pytest
from app.agent.llm import LLMTurn, ToolCallReq
from app.config import reset_settings_for_tests
from app.main import create_app
from conftest import ROOT, _load, gateway
from mcp import Client
from test_gmail import ME, TOKEN, SeededGoogle, connector, gmail, seed

live = _load("live_gmail_agent", ROOT / "integrations" / "demo_agent" / "live_gmail_agent.py")
REQUEST = f"Summarise my unread emails and send the summary to {ME}"
ATTACKER = seed.attacks(ME)["Mailbox migration notice"]

pytestmark = pytest.mark.anyio


@pytest.fixture
def anyio_backend():
    return "asyncio"


@pytest.fixture(autouse=True)
def gateway_env(monkeypatch):
    monkeypatch.setenv("PASSPORT_GATEWAY_TOKEN", TOKEN)
    monkeypatch.setenv("GATEWAY_APPROVAL_WAIT_S", "1")
    reset_settings_for_tests()


class FakeLLM:
    """Does what a fooled model does: reads the inbox, obeys the attack email, then the real task."""

    def __init__(self) -> None:
        self.plan = [
            ("start_task", {"request": REQUEST}),
            ("list_unread_emails", {}),
            ("send_email", {"to": ATTACKER, "subject": "Inbox summary", "body": "As requested."}),
            ("send_email", {"to": ME, "subject": "Inbox summary", "body": "Your summary."}),
        ]
        self.seen: list[list[dict]] = []

    async def next_turn(self, messages, tools, session):
        self.seen.append(list(messages))
        if not self.plan:
            return LLMTurn(content="Done.")
        name, args = self.plan.pop(0)
        return LLMTurn(content=None, tool_calls=[ToolCallReq(id=f"c{len(self.seen)}", name=name, args=args)])


class SpyUpstream:
    """The real Gmail connector client, recording every call that actually reaches it."""

    def __init__(self, client) -> None:
        self.client, self.calls = client, []

    async def list_tools(self):
        return await self.client.list_tools()

    async def call_tool(self, name, args):
        self.calls.append((name, args.get("to")))
        return await self.client.call_tool(name, args)


async def test_a_fooled_llm_is_refused_and_only_the_users_draft_is_made():
    fake, llm = SeededGoogle(), FakeLLM()
    async with Client(gmail.build_server(connector(fake))) as up:
        spy = SpyUpstream(up)
        gw = gateway.Gateway(
            spy, (await up.list_tools()).tools, passport_url="http://passport.test", token=TOKEN,
            agent_name="pytest live", approval_wait_s=1, server_name="gmail-mcp",
            transport=httpx.ASGITransport(app=create_app()),
        )
        async with Client(gateway.build_server(gw)) as agent:
            lines: list[str] = []
            stats = await live.run_agent(agent, llm, REQUEST, ME, say=lines.append)

    assert stats == {"attacker_addresses_tried": 1, "denied": 1, "drafts_made": 1}
    # The refusal went back to the model as a tool result, with the rule.
    refusal = [m for m in llm.seen[-1] if m["role"] == "tool"][2]["content"]
    assert refusal.startswith("PASSPORT DENY R3_SINK_UNTRUSTED")
    # Only allowed calls reached Gmail: never the attacker's send.
    assert spy.calls == [("list_unread_emails", None), ("send_email", ME)]
    assert len(fake.drafts) == 1 and f"To: {ME}" in fake.drafts[0]
    # Nothing from the real inbox is printed: no email bodies on screen.
    inbox = seed.emails(ME)
    assert not any(e["text"][:40] in line for e in inbox for line in lines)
    assert any("9 unread emails" in line for line in lines)


def test_tools_become_openai_function_schemas():
    tool = gateway.START_TASK
    [schema] = live.openai_tools([tool])
    assert schema["type"] == "function" and schema["function"]["name"] == "start_task"
    assert schema["function"]["parameters"]["required"] == ["request"]
    json.dumps(schema)  # must serialise for the API


def test_env_values_ignore_comments_and_quotes(tmp_path, monkeypatch):
    monkeypatch.delenv("LLM_MODEL", raising=False)
    f = tmp_path / ".env"
    f.write_text('LLM_MODEL="openai/gpt-oss-120b"  # groq\nOTHER=x\n', encoding="utf-8")
    assert live.env_value(f, "LLM_MODEL") == "openai/gpt-oss-120b"
    assert live.env_value(f, "MISSING") == ""
