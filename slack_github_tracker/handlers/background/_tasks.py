import asyncio
import contextlib
from collections.abc import AsyncIterator
from typing import TYPE_CHECKING, cast

import attrs
from machinery import helpers as hp

from slack_github_tracker.protocols import Logger

from . import _protocols as protocols


@attrs.frozen
class BackgroundTaskRunner:
    final_fut: asyncio.Future[None]


@attrs.define
class _TaskAppend:
    _adders: list[protocols.TaskAdder] | hp.Queue = attrs.field(factory=list)

    def __call__(self, task_adder: protocols.TaskAdder) -> None:
        self._adders.append(task_adder)

    def _change_to_queue(self, final_future: asyncio.Future[None]) -> hp.Queue:
        queue = hp.Queue(final_future, name="_TaskAppend::run[queue]")

        adders = self._adders
        self._adders = queue

        for adder in adders:
            queue.append(adder)

        return queue


@attrs.frozen
class Tasks:
    """
    Used to run tasks in background coroutines.

    Usage:

    .. code-block:: python

        from slack_github_tracker.handlers import background

        async def my_code() -> None:
            background_tasks = background.tasks.Tasks(logger=...)

            add_tasks1: background.protocols.TaskAdder = ...
            add_tasks2: background.protocols.TaskAdder = ...

            # Tasks added before the background tasks is started will only
            # be recorded. They do not start till after the tasks have been started
            background_tasks.append(add_tasks1)

            async with background_tasks.runner() as info:
                # info.final_future is a future that represents when the tasks should stop

                # We've started the background tasks, so these tasks will be run now
                background_tasks.append(add_tasks2)

                # Do other things now
                # And await till those are done
                # The tasks will be cancelled once this context manager is exited

            # Won't leave the context manager till all the tasks have finished

    Each task been added should be of the type `background.protocols.TaskAdder` which is a function
    that takes in the final future as well as an object that is used to register zero or more coroutines
    to be run.

    For example:

    .. code-block:: python

        import asyncio
        from machinery import helpers as hp


        def add_tasks(final_fut: asyncio.Future[None], task_holder: hp.TaskHolder) -> None:
            async def some_task() -> None:
                for _ in range(100):
                    await do_some_stuff()

            task_holder.add(some_task())
    """

    _logger: Logger

    append: _TaskAppend = attrs.field(factory=_TaskAppend)

    @contextlib.asynccontextmanager
    async def runner(self) -> AsyncIterator[BackgroundTaskRunner]:
        final_fut = hp.create_future(name="Tasks::runner[final_fut]")
        task_holder = hp.TaskHolder(final_fut, name="Tasks::runner[task_holder]")

        async with task_holder:
            task_holder.add(self._add_tasks(final_fut, task_holder))
            try:
                yield BackgroundTaskRunner(final_fut=final_fut)
            finally:
                final_fut.cancel()

    async def _add_tasks(
        self, final_fut: asyncio.Future[None], task_holder: hp.TaskHolder
    ) -> None:
        queue = self.append._change_to_queue(final_fut)
        async for task in queue:
            task(final_fut, task_holder)


if TYPE_CHECKING:
    _T: protocols.TasksAdder = cast(Tasks, None)
