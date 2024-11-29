from __future__ import annotations

import abc
from typing import TYPE_CHECKING, Self

import attrs
import cattrs
import slack_bolt
import structlog

from . import _protocols as protocols


class CommandError(Exception):
    def __str__(self) -> str:
        return "Failed to process command"


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


@attrs.frozen
class CommandMessage:
    token: str
    team_id: str
    team_domain: str
    channel_id: str
    channel_name: str
    user_id: str
    user_name: str
    command: str
    text: str
    api_app_id: str
    is_enterprise_install: bool
    response_url: str
    trigger_id: str

    @classmethod
    def deserialize(cls, message: dict[str, object]) -> Self:
        return cattrs.structure(message, cls)


@attrs.frozen
class MessageInterpreter[T_Message](abc.ABC):
    deserializer: protocols.Deserializer[T_Message]
    logger: structlog.stdlib.BoundLogger

    async def __call__(
        self, message: dict[str, object], say: slack_bolt.async_app.AsyncSay
    ) -> None:
        return await self.respond(self.deserializer.deserialize(message), say)

    @abc.abstractmethod
    async def respond(self, message: T_Message, say: slack_bolt.async_app.AsyncSay) -> None: ...


@attrs.frozen
class CommandInterpreter[T_Command](abc.ABC):
    deserializer: protocols.Deserializer[T_Command]
    logger: structlog.stdlib.BoundLogger

    async def __call__(
        self,
        ack: slack_bolt.async_app.AsyncAck,
        command: dict[str, object],
        respond: slack_bolt.async_app.AsyncRespond,
    ) -> None:
        await ack()
        try:
            deserialized = self.deserializer.deserialize(command)
        except CommandError as e:
            self.logger.exception("Failed to process command")
            await respond({"response_type": "ephemeral", "text": str(e)})
        except Exception:
            self.logger.exception("Failed to process command")
            await respond({"response_type": "ephemeral", "text": "Failed to process command"})
        else:
            await self.respond(deserialized, respond)

    @abc.abstractmethod
    async def respond(
        self, command: T_Command, respond: slack_bolt.async_app.AsyncRespond
    ) -> None: ...


if TYPE_CHECKING:
    _CMD: protocols.Deserializer[ChannelMessage] = ChannelMessage
    _COMD: protocols.Deserializer[CommandMessage] = CommandMessage
