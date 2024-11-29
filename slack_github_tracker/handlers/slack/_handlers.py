from __future__ import annotations

import attrs
import slack_bolt
import structlog

from . import _interpret as interpret
from . import _tracking as tracking


@attrs.frozen
class Deps:
    logger: structlog.stdlib.BoundLogger


def register_slack_handlers(deps: Deps, app: slack_bolt.async_app.AsyncApp) -> None:
    app.message("hello")(
        respond(logger=deps.logger).from_deserializer(
            interpret.MessageDeserializer(interpret.Message),
        ),
    )
    app.command("/track_pr")(
        track_pr(logger=deps.logger).from_deserializer(
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
        await say(f"Hey there <@{message.user}>!")


@attrs.frozen
class track_pr(interpret.CommandInterpreter[tracking.TrackPRMessage]):
    async def respond(
        self,
        *,
        command: tracking.TrackPRMessage,
        say: slack_bolt.async_app.AsyncSay,
        respond: slack_bolt.async_app.AsyncRespond,
    ) -> None:
        await say(f"Tracking {command.pr_to_track.display}")
        await respond(f"Hi <@{command.user_id}>!")
