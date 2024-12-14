from collections.abc import Iterator
from typing import TYPE_CHECKING, cast

import attrs

from .. import _event as event
from .. import _protocols as protocols


@attrs.frozen
class PullRequestReviewEventInterpreter:
    def interpret(self, incoming: protocols.Incoming) -> Iterator[protocols.Event]:
        if incoming.event != "pull_request_review":
            return

        if False:
            yield event.EmptyEvent()


if TYPE_CHECKING:
    _EI: protocols.EventInterpreter = cast(PullRequestReviewEventInterpreter, None)
