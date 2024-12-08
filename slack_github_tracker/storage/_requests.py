from typing import TYPE_CHECKING, cast

import attrs

from . import _protocols as protocols


@attrs.frozen
class PRRequest:
    pr: protocols.PR
    user_id: str
    channel_id: str


if TYPE_CHECKING:
    _PRR: protocols.PRRequest = cast(PRRequest, None)
