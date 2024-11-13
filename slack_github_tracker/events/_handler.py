from typing import TYPE_CHECKING, cast

from . import _protocols as protocols


class EventHandler:
    def add(self, *, identifier: str, event: protocols.Event) -> None:
        pass


if TYPE_CHECKING:
    _EH: protocols.EventHandler = cast(EventHandler, None)
