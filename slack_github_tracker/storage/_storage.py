from typing import TYPE_CHECKING, cast

import attrs
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession

from . import _protocols as protocols
from . import _prs as prs


@attrs.frozen
class Storage:
    engine: AsyncEngine

    async def store_pr_request(self, request: protocols.PRRequest, /) -> None:
        async with AsyncSession(self.engine) as session:
            async with session.begin():
                session.add(
                    prs.Request(
                        organisation=request.pr.organisation,
                        repo=request.pr.repo,
                        pr_number=request.pr.pr_number,
                        user_id=request.user_id,
                        channel_id=request.channel_id,
                    )
                )


if TYPE_CHECKING:
    _S: protocols.Storage = cast(Storage, None)
