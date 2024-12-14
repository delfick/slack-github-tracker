from collections.abc import Iterator
from typing import TYPE_CHECKING, cast

import attrs

from .. import _protocols as protocols
from . import _pull_request as pull_request
from . import _pull_request_review as pull_request_review


@attrs.frozen
class EventInterpreter:
    pull_request: protocols.EventInterpreter | None = attrs.field(
        factory=pull_request.PullRequestEventInterpreter
    )
    pull_request_review: protocols.EventInterpreter | None = attrs.field(
        factory=pull_request_review.PullRequestReviewEventInterpreter
    )

    def __iter__(self) -> Iterator[protocols.EventInterpreter | None]:
        yield self.pull_request
        yield self.pull_request_review

    def interpret(self, incoming: protocols.Incoming) -> Iterator[protocols.Event]:
        for interpreter in self:
            if interpreter is not None:
                yield from interpreter.interpret(incoming)


if TYPE_CHECKING:
    _EI: protocols.EventInterpreter = cast(EventInterpreter, None)
