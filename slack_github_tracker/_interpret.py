from __future__ import annotations

from typing import Self

import attrs
import cattrs
import slack_bolt

from . import protocols


@attrs.frozen
class ChannelMessage:
    type: str
    ts: float
    client_msg_id: str
    text: str
    team: str
    user: str
    channel: str
    event_ts: float
    channel_type: str

    @classmethod
    def deserialize(cls, message: dict[str, object]) -> Self:
        assert message.get("type") == "message"
        return cattrs.structure(message, cls)


class MessageInterpreter:
    def __init__[T_Message](
        self,
        deserializer: protocols.Deserializer[T_Message],
        respond: protocols.Responder[T_Message],
    ) -> None:
        self.deserializer = deserializer
        self.respond = respond

    async def __call__(
        self, message: dict[str, object], say: slack_bolt.async_app.AsyncSay
    ) -> None:
        return await self.respond(self.deserializer.deserialize(message), say)
