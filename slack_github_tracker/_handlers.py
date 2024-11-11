from __future__ import annotations

import slack_bolt

from . import _interpret as interpret


def register_handlers(app: slack_bolt.async_app.AsyncApp) -> None:
    app.message("hello")(interpret.MessageInterpreter(interpret.ChannelMessage, respond))


async def respond(message: interpret.ChannelMessage, say: slack_bolt.async_app.AsyncSay) -> None:
    await say(f"Hey there <@{message.user}>!")
