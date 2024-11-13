from typing import Protocol


class Event(Protocol):
    pass


class EventHandler(Protocol):
    def add(self, *, identifier: str, event: Event) -> None: ...
