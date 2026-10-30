"""The segment store: every piece of text this session has seen, labelled by trust.

The gate traces argument values back to these segments. Tool outputs are added AFTER the tool
runs (ingest), so a value can only have a passport from content that really entered the context.
"""

from __future__ import annotations

import json
from typing import Any

from app.contracts import Segment, Trust
from app.tools.registry import TOOLS
from app.tools.world import World


class SegmentStore:
    def __init__(self) -> None:
        self.items: list[Segment] = []
        self.read_untrusted = False  # has outside content entered the context yet?
        self.revealed: set[str] = set()  # secret names the agent has actually seen

    def add(self, seg_id: str, source: str, trust: Trust, text: str, hidden: bool = False) -> Segment:
        for s in self.items:
            if s.id == seg_id:
                return s
        seg = Segment(id=seg_id, source=source, trust=trust, text=str(text), hidden=hidden)
        self.items.append(seg)
        if trust == Trust.UNTRUSTED:
            self.read_untrusted = True
        return seg

    def get(self, seg_id: str) -> Segment | None:
        return next((s for s in self.items if s.id == seg_id), None)

    def _add_email(self, e: dict[str, Any]) -> None:
        text = f"From: {e['from']}\nSubject: {e['subject']}\n\n{e['body']}"
        self.add(f"email:{e['id']}", f"Email #{e['id']} from {e['from']}", Trust.UNTRUSTED, text)

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


def new_store(user_request: str, world: World) -> SegmentStore:
    s = SegmentStore()
    s.add("user", "Your request", Trust.USER, user_request)
    s.add(
        "vendors",
        "Vendor registry (trusted config)",
        Trust.TRUSTED,
        "\n".join(f"{name}: {acct}" for name, acct in world.vendors.items()),
    )
    for name, value in world.vault.items():
        # Known to the gate so a secret can never be laundered, never shown to the agent.
        s.add(f"vault:{name}", f"Vault secret {name}", Trust.SECRET, value, hidden=True)
    return s
