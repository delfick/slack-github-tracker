from typing import Protocol


class RawHeaders(Protocol):
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
    def register(self, body: dict[str, object], raw_headers: RawHeaders) -> None: ...

    def determine_expected_signature(self, body: bytes) -> str: ...
