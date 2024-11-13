from __future__ import annotations

from typing import Protocol


class Event(Protocol):
    def process(self) -> None: ...


class EventHandler(Protocol):
    def append(self, event: Event, /) -> None: ...
