from collections.abc import Iterator
from typing import Protocol

import slack_bolt.async_app
import sqlalchemy

from slack_github_tracker.protocols import Logger

from .. import background


class Incoming(Protocol):
    @property
    def body(self) -> dict[str, object]:
        """
        The JSON in the body of the incoming webhook
        """

    @property
    def logger(self) -> Logger:
        """
        A logger instance already bound with relevant logging information
        """

    @property
    def event(self) -> str:
        """Name of the event that triggered the delivery."""

    @property
    def hook_id(self) -> str:
        """Unique identifier of the webhook."""

    @property
    def delivery(self) -> str:
        """A globally unique identifier (GUID) to identify the event."""

    @property
    def hook_installation_target_id(self) -> str:
        """Unique identifier of the resource where the webhook was created."""

    @property
    def hook_installation_target_type(self) -> str:
        """Type of resource where the webhook was created."""


class Hooks(Protocol):
    def register(self, incoming: Incoming, /) -> None: ...

    def determine_expected_signature(self, body: bytes) -> str: ...


class EventProcessInfo(Protocol):
    @property
    def logger(self) -> Logger: ...

    @property
    def database(self) -> sqlalchemy.ext.asyncio.AsyncEngine: ...

    @property
    def background_tasks(self) -> background.protocols.TasksAdder: ...

    @property
    def slack_app(self) -> slack_bolt.async_app.AsyncApp: ...


class Event(Protocol):
    async def process(self, info: EventProcessInfo, /) -> None: ...


class EventHandler(Protocol):
    def append(self, event: Event, /) -> None: ...


class EventInterpreter(Protocol):
    def interpret(self, incoming: Incoming, /) -> Iterator[Event]: ...
