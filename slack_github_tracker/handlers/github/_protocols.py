from typing import Protocol

from slack_github_tracker.protocols import Logger


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
