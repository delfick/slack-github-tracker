from __future__ import annotations

from typing import Protocol

import slack_bolt


class Event(Protocol):
    async def process(self, slack_app: slack_bolt.async_app.AsyncApp) -> None: ...


class EventHandler(Protocol):
    def append(self, event: Event, /) -> None: ...
