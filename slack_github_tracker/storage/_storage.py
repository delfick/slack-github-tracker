from typing import TYPE_CHECKING, cast

import attrs
import sqlalchemy
from sqlalchemy.ext.asyncio import AsyncEngine

from . import _protocols as protocols
from ._prs import pr_requests_table


@attrs.frozen
class Storage:
    engine: AsyncEngine

    async def store_pr_request(self, pr: protocols.PR) -> None:
        stmt = sqlalchemy.insert(pr_requests_table).values(
            organisation=pr.organisation, repo=pr.repo, pr_number=pr.pr_number
        )

        async with self.engine.connect() as conn:
            await conn.execute(stmt)
            await conn.commit()


if TYPE_CHECKING:
    _S: protocols.Storage = cast(Storage, None)
