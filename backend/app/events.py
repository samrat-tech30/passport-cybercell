"""Per-session event log + live stream (Server-Sent Events).

Events are kept in memory per session so a browser that connects late still gets everything
(it asks for events after seq N). Persistent truth lives in the database and the audit log.
"""

from __future__ import annotations

import asyncio
from collections.abc import AsyncIterator
from typing import Any

from app.contracts import Event

TERMINAL = {"done", "error"}


class Bus:
    def __init__(self, session_id: str) -> None:
        self.session_id = session_id
        self.events: list[Event] = []
        self._cond = asyncio.Condition()

    async def emit(self, type_: str, data: dict[str, Any] | None = None) -> Event:
        ev = Event(seq=len(self.events) + 1, session_id=self.session_id, type=type_, data=data or {})
        self.events.append(ev)
        async with self._cond:
            self._cond.notify_all()
        return ev

    @property
    def finished(self) -> bool:
        return bool(self.events) and self.events[-1].type in TERMINAL

    async def stream(self, after: int = 0, keepalive_s: float = 15.0) -> AsyncIterator[Event | None]:
        """Yield events with seq > after; yield None as a keep-alive tick while waiting."""
        idx = max(0, after)
        while True:
            while idx < len(self.events):
                ev = self.events[idx]
                idx += 1
                yield ev
                if ev.type in TERMINAL:
                    return
            async with self._cond:
                try:
                    await asyncio.wait_for(self._cond.wait(), timeout=keepalive_s)
                except TimeoutError:
                    yield None
