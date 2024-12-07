from __future__ import annotations

from typing import Protocol

import attrs
import slack_bolt
from sqlalchemy.ext.asyncio import AsyncEngine

from slack_github_tracker import storage
from slack_github_tracker.protocols import Logger

from . import _interpret as interpret
from . import _tracking as tracking


@attrs.frozen
class Deps:
    logger: Logger
    database: AsyncEngine


def register_slack_handlers(deps: Deps, app: slack_bolt.async_app.AsyncApp) -> None:
    app.message("hello")(
        respond(logger=deps.logger).from_deserializer(
            interpret.MessageDeserializer(interpret.Message),
        ),
    )
    app.command("/track_pr")(
        track_pr(logger=deps.logger, storage=storage.Storage(deps.database)).from_deserializer(
            tracking.TrackPRMessageDeserializer(),
        ),
    )


@attrs.frozen
class respond(interpret.MessageInterpreter[interpret.Message]):
    async def respond(
        self,
        *,
        message: interpret.Message,
        say: slack_bolt.async_app.AsyncSay,
        respond: slack_bolt.async_app.AsyncRespond,
    ) -> None:
        await say(f"Hey there <@{message.raw_message.user}>!")


@attrs.frozen
class track_pr(interpret.CommandInterpreter[tracking.TrackPRMessage]):
    class _StorePRRequest(Protocol):
        async def store_pr_request(self, pr: storage.protocols.PR) -> None: ...

    storage: _StorePRRequest

    async def respond(
        self,
        *,
        command: tracking.TrackPRMessage,
        say: slack_bolt.async_app.AsyncSay,
        respond: slack_bolt.async_app.AsyncRespond,
    ) -> None:
        await self.storage.store_pr_request(command.pr_to_track)
        await say(f"Tracking {command.pr_to_track.display}")
        await respond(f"Hi <@{command.raw_command.user_id}>!")
