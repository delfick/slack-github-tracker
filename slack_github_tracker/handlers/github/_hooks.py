import hashlib
import hmac
from typing import TYPE_CHECKING, cast

import attrs

from slack_github_tracker import events

from . import _errors as errors
from . import _protocols as protocols


@attrs.frozen
class RawHeaders:
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
    _events: events.protocols.EventHandler

    def register(self, body: dict[str, object], raw_headers: protocols.RawHeaders) -> None:
        if raw_headers.event not in ("pull_request", "pull_request_review"):
            raise errors.GithubWebhookDropped(event=raw_headers.event)

        event = self._interpret(raw_headers.delivery, body)
        if event is None:
            raise errors.GithubWebhookDropped(event=raw_headers.event)

        self._events.append(event)

    def determine_expected_signature(self, body: bytes) -> str:
        hash_object = hmac.new(self._secret.encode("utf-8"), msg=body, digestmod=hashlib.sha256)
        return f"sha256={hash_object.hexdigest()}"

    def _interpret(
        self, identifier: str, body: dict[str, object]
    ) -> events.protocols.Event | None:
        return None


if TYPE_CHECKING:
    _RH: protocols.RawHeaders = cast(RawHeaders, None)
    _H: protocols.Hooks = cast(Hooks, None)
