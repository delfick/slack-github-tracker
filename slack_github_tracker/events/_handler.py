from typing import TYPE_CHECKING, cast

import attrs
import structlog

from . import _protocols as protocols


@attrs.frozen
class EventHandler:
    _logger: structlog.stdlib.BoundLogger

    def append(self, event: protocols.Event) -> None:
        pass


if TYPE_CHECKING:
    _EH: protocols.EventHandler = cast(EventHandler, None)
