"""The segment store: every piece of text this session has seen, labelled by trust.

The gate traces argument values back to these segments. Tool outputs are added AFTER the tool
runs (ingest), so a value can only have a passport from content that really entered the context.
"""

from __future__ import annotations

import json
import re
from typing import Any

from app.contracts import Segment, Trust
from app.tools.registry import TOOLS
from app.tools.world import World

_EMAIL_CORE = ("id", "from", "subject", "body")


def _leaves(value: Any) -> list[str]:
    """The raw strings inside a value, nested dicts (keys too) and lists walked. Never str() a dict or a
    list: repr() writes a zero-width space as the text "\\u200b", so the value the agent reads (real
    characters) would match nothing here."""
    if isinstance(value, dict):
        return [s for k, v in value.items() for s in (str(k), *_leaves(v))]
    if isinstance(value, (list, tuple)):
        return [s for v in value for s in _leaves(v)]
    return [] if value is None else [str(value)]


def _text(value: Any) -> str:
    return "\n".join(_leaves(value))


def _extra_fields(e: dict[str, Any]) -> str:
    """Every other field the agent can see (Reply-To, Cc, attachment names...) as extra lines AFTER the
    body, so body line numbers never move. Empty string when there are none."""
    # Everything except the core fields, not an allowlist: a header nobody planned for is still labelled.
    # One line per string, so 1000 attachment names don't make one line too long for the disguise views.
    lines = [
        f"{key}: {leaf}" for key, value in e.items() if key not in _EMAIL_CORE for leaf in _leaves(value)
    ]
    return "\n\n" + "\n".join(lines) if lines else ""


class SegmentStore:
    def __init__(self) -> None:
        self.items: list[Segment] = []
        self.read_untrusted = False  # has outside content entered the context yet?
        self.revealed: set[str] = set()  # secret names the agent has actually seen

    def add(self, seg_id: str, source: str, trust: Trust, text: str, hidden: bool = False) -> Segment:
        same_id = [s for s in self.items if s.id == seg_id or s.id.startswith(f"{seg_id}#")]
        for s in same_id:
            if s.text == str(text) and s.trust == trust:
                return s  # the same content read twice (list, then read_email)
        if same_id:  # same id, different text (a sender-chosen id?): label it too, never drop it
            seg_id = f"{seg_id}#{len(same_id) + 1}"
        seg = Segment(id=seg_id, source=source, trust=trust, text=str(text), hidden=hidden)
        self.items.append(seg)
        if trust == Trust.UNTRUSTED:
            self.read_untrusted = True
        return seg

    def get(self, seg_id: str) -> Segment | None:
        return next((s for s in self.items if s.id == seg_id), None)

    def _add_email(self, e: dict[str, Any]) -> None:
        # .get(): an email without a subject is normal mail, not a reason to crash the session.
        sender = _text(e.get("from"))
        text = (
            f"From: {sender}\nSubject: {_text(e.get('subject'))}\n\n{_text(e.get('body'))}" + _extra_fields(e)
        )
        self.add(f"email:{e.get('id')}", f"Email #{e.get('id')} from {sender}", Trust.UNTRUSTED, text)

    def ingest(self, tool: str, args: dict[str, Any], output: Any) -> None:
        """Label a tool's output. Called by the gate right after the tool runs."""
        if tool == "list_unread_emails":
            for e in output:
                self._add_email(e)
        elif tool == "read_email":
            self._add_email(output)
        elif tool == "read_file":
            self.add(f"file:{args['path']}", f"File {args['path']}", Trust.UNTRUSTED, output)
        elif tool == "read_secret":
            self.add(f"secret:{args['key']}", f"Vault secret {args['key']}", Trust.SECRET, output)
            self.revealed.add(args["key"])
        elif TOOLS[tool].output_trust != Trust.TRUSTED:
            text = output if isinstance(output, str) else json.dumps(output, ensure_ascii=False)
            self.add(f"{tool}:{len(self.items)}", f"{tool} output", TOOLS[tool].output_trust, text)
        # Action tools (send, pay, delete) return fixed confirmations with no values: nothing to label.


def named_contacts(user_request: str, contacts: dict[str, str]) -> dict[str, str]:
    """The contacts whose name the user typed as a whole word ("Rahul's" yes, "Priyanka" not Priya).

    Only these are trusted: decide() doesn't check recipients against the request, so trusting the whole
    directory would let an email steer a send to any colleague. Built from the user's words only, before
    any tool runs, so nothing an attacker writes can add a name."""
    return {
        name: addr
        for name, addr in contacts.items()
        if re.search(rf"(?<!\w){re.escape(name)}(?!\w)", user_request, re.IGNORECASE)
    }


def new_store(user_request: str, world: World) -> SegmentStore:
    s = SegmentStore()
    s.add("user", "Your request", Trust.USER, user_request)
    s.add(
        "vendors",
        "Vendor registry (trusted config)",
        Trust.TRUSTED,
        "\n".join(f"{name}: {acct}" for name, acct in world.vendors.items()),
    )
    named = named_contacts(user_request, world.contacts)
    if named:
        s.add(
            "contacts",
            "Contacts you named (trusted config)",
            Trust.TRUSTED,
            "\n".join(f"{name}: {addr}" for name, addr in named.items()),
        )
    for name, value in world.vault.items():
        # Known to the gate so a secret can never be laundered, never shown to the agent.
        s.add(f"vault:{name}", f"Vault secret {name}", Trust.SECRET, value, hidden=True)
    return s
