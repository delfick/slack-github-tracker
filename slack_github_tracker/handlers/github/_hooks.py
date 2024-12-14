import hashlib
import hmac
from typing import TYPE_CHECKING, cast

import attrs

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
    _event_adder: protocols.EventHandler
    _event_interpreter: protocols.EventInterpreter

    def register(self, incoming: protocols.Incoming, /) -> None:
        found: bool = False
        for event in self._event_interpreter.interpret(incoming):
            self._event_adder.append(event)
            found = True

        if not found:
            raise errors.GithubWebhookDropped(reason="Unrecognised webhook event")

    def determine_expected_signature(self, body: bytes) -> str:
        hash_object = hmac.new(self._secret.encode("utf-8"), msg=body, digestmod=hashlib.sha256)
        return f"sha256={hash_object.hexdigest()}"


if TYPE_CHECKING:
    _RH: protocols.Incoming = cast(Incoming, None)
    _H: protocols.Hooks = cast(Hooks, None)
