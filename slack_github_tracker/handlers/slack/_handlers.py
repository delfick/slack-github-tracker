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
    app.message("hello")(respond(interpret.ChannelMessage, logger=deps.logger))
    app.command("/track_pr")(track_pr(tracking.TrackPRMessage, logger=deps.logger))


@attrs.frozen
class respond(interpret.MessageInterpreter[interpret.ChannelMessage]):
    async def respond(
        self, message: interpret.ChannelMessage, say: slack_bolt.async_app.AsyncSay
    ) -> None:
        await say(f"Hey there <@{message.user}>!")


@attrs.frozen
class track_pr(interpret.CommandInterpreter[tracking.TrackPRMessage]):
    async def respond(
        self, command: tracking.TrackPRMessage, respond: slack_bolt.async_app.AsyncRespond
    ) -> None:
        await respond(f"Hi <@{command.user_id}>!")
