import attrs

from . import _protocols as protocols


@attrs.frozen
class EmptyEvent:
    async def process(self, info: protocols.EventProcessInfo, /) -> None:
        pass
