import asyncio
from typing import TYPE_CHECKING, cast

import attrs
import slack_bolt
import sqlalchemy
from machinery import helpers as hp

from slack_github_tracker.protocols import Logger

from .. import background
from . import _protocols as protocols


@attrs.define
class _EventAppend:
    _events: list[protocols.Event] | hp.Queue = attrs.field(factory=list)

    def __call__(self, event: protocols.Event) -> None:
        self._events.append(event)

    def _change_to_queue(self, final_future: asyncio.Future[None]) -> hp.Queue:
        queue = hp.Queue(final_future, name="_EventAppend::run[queue]")

        events = self._events
        self._events = queue

        for event in events:
            queue.append(event)

        return queue


@attrs.frozen
class _Info:
    logger: Logger
    database: sqlalchemy.ext.asyncio.AsyncEngine
    background_tasks: background.protocols.TasksAdder
    slack_app: slack_bolt.async_app.AsyncApp


@attrs.frozen
class EventHandler:
    _logger: Logger

    append: _EventAppend = attrs.field(factory=_EventAppend)

    async def run(
        self,
        *,
        final_future: asyncio.Future[None],
        task_holder: hp.TaskHolder,
        database: sqlalchemy.ext.asyncio.AsyncEngine,
        background_tasks: background.protocols.TasksAdder,
        slack_app: slack_bolt.async_app.AsyncApp,
    ) -> None:
        queue = self.append._change_to_queue(final_future)

        async for event in queue:
            task_holder.add(
                event.process(
                    _Info(
                        logger=self._logger,
                        database=database,
                        background_tasks=background_tasks,
                        slack_app=slack_app,
                    )
                )
            )


if TYPE_CHECKING:
    _EH: protocols.EventHandler = cast(EventHandler, None)
    _I: protocols.EventProcessInfo = cast(_Info, None)
