import asyncio
import contextlib
from collections.abc import AsyncGenerator, AsyncIterator
from typing import TYPE_CHECKING, cast

import attrs
from machinery import helpers as hp

import slack_github_tracker

from . import _protocols as protocols


@attrs.frozen
class BackgroundTaskRunner:
    final_fut: asyncio.Future[None]


@attrs.frozen
class TasksAdderStart:
    queue: list[protocols.TaskAdder] = attrs.field(factory=list)

    def append(self, task_adder: protocols.TaskAdder) -> None:
        self.queue.append(task_adder)

    def __aiter__(self) -> AsyncIterator[protocols.TaskAdder]:
        return self.get_all()

    async def get_all(self) -> AsyncGenerator[protocols.TaskAdder]:
        if isinstance(self.queue, list):
            for adder in self.queue:
                yield adder


@attrs.frozen
class TasksAdderAfterStart:
    queue: hp.Queue

    def append(self, task_adder: protocols.TaskAdder) -> None:
        self.queue.append(task_adder, context=self)

    def __aiter__(self) -> AsyncIterator[protocols.TaskAdder]:
        return self.queue.__aiter__()  # type: ignore[no-any-return]


@attrs.define
class Tasks:
    logger: slack_github_tracker.protocols.Logger
    tasks: protocols.TasksAdder = attrs.field(factory=TasksAdderStart)

    @contextlib.asynccontextmanager
    async def runner(self) -> AsyncIterator[BackgroundTaskRunner]:
        final_fut = hp.create_future(name="Tasks::runner[final_fut]")
        task_holder = hp.TaskHolder(final_fut, name="Tasks::runner[task_holder]")

        async with task_holder:
            task_holder.add(self.add_tasks(final_fut, task_holder))
            yield BackgroundTaskRunner(final_fut=final_fut)

    async def add_tasks(self, final_fut: asyncio.Future[None], task_holder: hp.TaskHolder) -> None:
        async for task in self.tasks:
            task_holder.add(task(final_fut, task_holder))

        if isinstance(self.tasks, TasksAdderStart):
            self.tasks = TasksAdderAfterStart(
                queue=hp.Queue(final_fut, name="Tasks::add_tasks[tasks]")
            )
            async for task in self.tasks:
                task_holder.add(task(final_fut, task_holder))


if TYPE_CHECKING:
    _TAS: protocols.TasksAdder = cast(TasksAdderStart, None)
    _TAAS: protocols.TasksAdder = cast(TasksAdderAfterStart, None)
