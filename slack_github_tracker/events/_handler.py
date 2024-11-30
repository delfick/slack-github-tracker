from typing import TYPE_CHECKING, cast

import attrs

from slack_github_tracker.protocols import Logger

from . import _protocols as protocols


@attrs.frozen
class EventHandler:
    _logger: Logger

    def append(self, event: protocols.Event) -> None:
        pass


if TYPE_CHECKING:
    _EH: protocols.EventHandler = cast(EventHandler, None)
