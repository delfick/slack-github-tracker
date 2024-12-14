from __future__ import annotations

import asyncio
from typing import TYPE_CHECKING, cast

import attrs
import slack_bolt
from machinery import helpers as hp

from slack_github_tracker.protocols import Logger

from . import _protocols as protocols


@attrs.define
class EventHandler:
    _logger: Logger
    _events: list[protocols.Event] | hp.Queue = attrs.field(factory=list)

    def append(self, event: protocols.Event) -> None:
        self._events.append(event)

    async def run(
        self, final_future: asyncio.Future[None], slack_app: slack_bolt.async_app.AsyncApp
    ) -> None:
        queue = hp.Queue(final_future, name="EventHandler::run[queue]")

        events = self._events
        self._events = queue

        for event in events:
            queue.append(event)

        async for event in queue:
            await self.process(event, slack_app)

    async def process(
        self, event: protocols.Event, slack_app: slack_bolt.async_app.AsyncApp
    ) -> None:
        pass


if TYPE_CHECKING:
    _EH: protocols.EventHandler = cast(EventHandler, None)
