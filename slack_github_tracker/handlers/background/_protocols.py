import asyncio
from collections.abc import AsyncIterator
from typing import Protocol

from machinery import helpers as hp


class TaskAdder(Protocol):
    async def __call__(
        self, final_fut: asyncio.Future[None], task_holder: hp.TaskHolder, /
    ) -> None: ...


class TasksAdder(Protocol):
    def append(self, task_adder: TaskAdder) -> None: ...

    def __aiter__(self) -> AsyncIterator[TaskAdder]: ...
