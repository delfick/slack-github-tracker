import hmac
from types import SimpleNamespace

import attrs
import cattrs
import sanic
import slack_bolt
from slack_bolt.adapter.sanic import async_handler as bolt_async_handler

from .. import github


@attrs.frozen
class Registry:
    slack_app: slack_bolt.async_app.AsyncApp
    github_webhooks: github.protocols.Hooks


class GithubWebhook:
    def __init__(self, hooks: github.protocols.Hooks) -> None:
        self.hooks = hooks

    async def handle(self, request: sanic.Request) -> sanic.response.HTTPResponse:
        if not request.headers["user-agent"].startswith("GitHub-Hookshot/"):
            # Github documentation say the user agent should always start with this specific string
            return sanic.empty(400)

        try:
            hub_signature_256 = request.headers["x-hub-signature-256"]
        except KeyError:
            return sanic.empty(400)
        else:
            if not hub_signature_256:
                return sanic.empty(400)

        expected_signature = self.hooks.determine_expected_signature(request.body)
        if not hmac.compare_digest(expected_signature, hub_signature_256):
            return sanic.empty(403)

        try:
            raw_header_values = {
                "delivery": request.headers["x-github-delivery"],
                "event": request.headers["x-github-event"],
                "hook_id": request.headers["x-github-hook-id"],
                "hook_installation_target_id": (
                    request.headers["x-github-hook-installation-target-id"]
                ),
                "hook_installation_target_type": (
                    request.headers["x-github-hook-installation-target-type"]
                ),
            }
        except KeyError:
            return sanic.empty(400)

        if not all(raw_header_values.values()):
            return sanic.empty(400)

        try:
            raw_headers = cattrs.structure(raw_header_values, github.RawHeaders)
        except cattrs.errors.BaseValidationError:
            return sanic.empty(400)

        try:
            self.hooks.register(request.json, raw_headers)
        except github.errors.GithubWebhookDropped:
            return sanic.empty()
        except github.errors.GithubWebhookError:
            return sanic.empty(500)
        else:
            return sanic.empty()


def register_sanic_routes(
    sanic_app: sanic.Sanic[sanic.Config, SimpleNamespace], registry: Registry
) -> sanic.Sanic[sanic.Config, SimpleNamespace]:
    @sanic_app.post("/slack/events", name="slack_events")
    async def slack_events(request: sanic.Request) -> sanic.response.HTTPResponse:
        bolt_resp = await registry.slack_app.async_dispatch(
            bolt_async_handler.to_async_bolt_request(request)
        )
        return bolt_async_handler.to_sanic_response(bolt_resp)

    @sanic_app.post("/github/webhook", name="github_webhook")
    async def github_webhook(request: sanic.Request) -> sanic.response.HTTPResponse:
        return await GithubWebhook(registry.github_webhooks).handle(request)

    return sanic_app
