import hashlib
import hmac
from typing import TYPE_CHECKING, cast

import attrs

from slack_github_tracker import events
from slack_github_tracker.protocols import Logger

from . import _errors as errors
from . import _protocols as protocols


@attrs.frozen
class Incoming:
    # The json in the body of the request
    body: dict[str, object]

    # Logger instance already bound with relevant information
    logger: Logger

    # Name of the event that triggered the delivery.
    event: str

    # Unique identifier of the webhook.
    hook_id: str

    # A globally unique identifier (GUID) to identify the event.
    delivery: str

    # Unique identifier of the resource where the webhook was created.
    hook_installation_target_id: str

    # Type of resource where the webhook was created.
    hook_installation_target_type: str


@attrs.frozen
class Hooks:
    _secret: str
    _logger: Logger
    _events: events.protocols.EventHandler

    def register(self, incoming: protocols.Incoming, /) -> None:
        if incoming.event not in ("pull_request", "pull_request_review"):
            raise errors.GithubWebhookDropped(reason="Unexpected event type")

        event = self._interpret(incoming)
        if event is None:
            raise errors.GithubWebhookDropped(reason="Unrecognised webhook event")

        self._events.append(event)

    def determine_expected_signature(self, body: bytes) -> str:
        hash_object = hmac.new(self._secret.encode("utf-8"), msg=body, digestmod=hashlib.sha256)
        return f"sha256={hash_object.hexdigest()}"

    def _interpret(self, incoming: protocols.Incoming) -> events.protocols.Event | None:
        return None


if TYPE_CHECKING:
    _RH: protocols.Incoming = cast(Incoming, None)
    _H: protocols.Hooks = cast(Hooks, None)
