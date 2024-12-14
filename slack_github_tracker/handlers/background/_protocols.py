import asyncio
from typing import Protocol

from machinery import helpers as hp


class TaskAdder(Protocol):
    def __call__(self, final_fut: asyncio.Future[None], task_holder: hp.TaskHolder, /) -> None: ...


class TasksAdder(Protocol):
    def append(self, task_adder: TaskAdder) -> None: ...
