from __future__ import annotations

import abc
from typing import TYPE_CHECKING, cast

import attrs
import cattrs
import slack_bolt
import structlog

from . import _protocols as protocols


class CommandError(Exception):
    def __str__(self) -> str:
        return "Failed to process command"


def structure_bool_from_str(
    val: cattrs.dispatch.UnstructuredValue, target: cattrs.dispatch.TargetType
) -> bool:
    if isinstance(val, bool):
        return val

    if isinstance(val, str):
        if val == "true":
            return True
        elif val == "false":
            return False

    raise ValueError(f"Failed to parse boolean from: '{val}'")


@attrs.frozen
class Message:
    type: str
    ts: float
    client_msg_id: str
    text: str
    team: str
    user: str
    channel: str
    event_ts: float
    channel_type: str


@attrs.frozen
class MessageDeserializer[T_Shape: Message]:
    shape: type[T_Shape]

    converter: cattrs.Converter = attrs.field(init=False)

    @converter.default
    def _make_cattrs_converter(self) -> cattrs.Converter:
        return cattrs.Converter()

    def deserialize(self, message: dict[str, object]) -> T_Shape:
        assert message.get("type") == "message"
        return self.converter.structure(message, self.shape)


@attrs.frozen
class Command:
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


@attrs.frozen
class CommandDeserializer[T_Shape: Command]:
    shape: type[T_Shape]

    converter: cattrs.Converter = attrs.field(init=False)

    @converter.default
    def _make_cattrs_converter(self) -> cattrs.Converter:
        converter = cattrs.Converter()
        converter.register_structure_hook(bool, structure_bool_from_str)
        return converter

    def deserialize(self, message: dict[str, object]) -> T_Shape:
        return self.converter.structure(message, self.shape)


@attrs.frozen(kw_only=True)
class MessageInterpreter[T_Message](abc.ABC):
    logger: structlog.stdlib.BoundLogger

    @attrs.frozen(kw_only=True)
    class Responder[T_MessageType]:
        deserializer: protocols.Deserializer[T_MessageType]
        instance: MessageInterpreter[T_MessageType]

        async def __call__(
            self,
            message: dict[str, object],
            say: slack_bolt.async_app.AsyncSay,
            respond: slack_bolt.async_app.AsyncRespond,
        ) -> None:
            return await self.instance.respond(
                message=self.deserializer.deserialize(message), say=say, respond=respond
            )

    def from_deserializer(
        self, deserializer: protocols.Deserializer[T_Message]
    ) -> Responder[T_Message]:
        return self.Responder(deserializer=deserializer, instance=self)

    @abc.abstractmethod
    async def respond(
        self,
        *,
        message: T_Message,
        say: slack_bolt.async_app.AsyncSay,
        respond: slack_bolt.async_app.AsyncRespond,
    ) -> None: ...


@attrs.frozen(kw_only=True)
class CommandInterpreter[T_Command](abc.ABC):
    logger: structlog.stdlib.BoundLogger

    @attrs.frozen(kw_only=True)
    class Responder[T_CommandType]:
        deserializer: protocols.Deserializer[T_CommandType]
        instance: CommandInterpreter[T_CommandType]

        async def __call__(
            self,
            ack: slack_bolt.async_app.AsyncAck,
            command: dict[str, object],
            say: slack_bolt.async_app.AsyncSay,
            respond: slack_bolt.async_app.AsyncRespond,
        ) -> None:
            await ack()
            try:
                deserialized = self.deserializer.deserialize(command)
            except CommandError as e:
                self.instance.logger.exception("Failed to process command")
                await respond(str(e))
            except Exception:
                self.instance.logger.exception("Failed to process command")
                await say("Failed to process command")
            else:
                await self.instance.respond(command=deserialized, say=say, respond=respond)

    def from_deserializer(
        self, deserializer: protocols.Deserializer[T_Command]
    ) -> Responder[T_Command]:
        return self.Responder(deserializer=deserializer, instance=self)

    @abc.abstractmethod
    async def respond(
        self,
        *,
        command: T_Command,
        say: slack_bolt.async_app.AsyncSay,
        respond: slack_bolt.async_app.AsyncRespond,
    ) -> None: ...


if TYPE_CHECKING:
    _CMD: protocols.Deserializer[Message] = cast(MessageDeserializer[Message], None)
    _COMD: protocols.Deserializer[Command] = cast(CommandDeserializer[Command], None)
