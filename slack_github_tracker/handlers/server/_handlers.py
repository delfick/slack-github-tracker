import hmac
from types import SimpleNamespace

import attrs
import sanic
import slack_bolt
import structlog
from slack_bolt.adapter.sanic import async_handler as bolt_async_handler

from .. import github


@attrs.frozen
class Registry:
    slack_app: slack_bolt.async_app.AsyncApp
    github_webhooks: github.protocols.Hooks


@attrs.frozen
class GithubWebhook:
    _logger: structlog.stdlib.BoundLogger
    _hooks: github.protocols.Hooks

    async def handle(self, request: sanic.Request) -> sanic.response.HTTPResponse:
        logger = self._logger
        if "x-github-delivery" in request.headers:
            logger = logger.bind(github_delivery=request.headers["x-github-delivery"])

        if not request.headers["user-agent"].startswith("GitHub-Hookshot/"):
            # Github documentation say the user agent should always start with this specific string
            logger.error("User agent field was incorrect", found=request.headers["user-agent"])
            return sanic.empty(400)

        try:
            hub_signature_256 = request.headers["x-hub-signature-256"]
        except KeyError:
            logger.error("No x-hub-signature-256 header provided")
            return sanic.empty(400)
        else:
            if not hub_signature_256:
                logger.error("No x-hub-signature-256 header provided")
                return sanic.empty(400)

        expected_signature = self._hooks.determine_expected_signature(request.body)
        if not hmac.compare_digest(expected_signature, hub_signature_256):
            logger.error("Request from github web hook has invalid signature")
            return sanic.empty(403)

        try:
            body: dict[str, object] = request.json
        except (TypeError, ValueError):
            logger.exception("Failed to parse the webhook body as json")
            return sanic.empty(500)

        try:
            raw_headers = {
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

        if not all(raw_headers.values()):
            logger.error("Webhook has unexpected empty values")
            return sanic.empty(400)

        incoming = github.Incoming(body=body, logger=logger, **raw_headers)

        try:
            self._hooks.register(incoming)
        except github.errors.GithubWebhookDropped as e:
            logger.info("Event dropped", reason=e.reason)
            return sanic.empty()
        except github.errors.GithubWebhookError:
            logger.exception("Failed to process webhook")
            return sanic.empty(500)
        else:
            return sanic.empty()


def register_sanic_routes(
    *,
    logger: structlog.stdlib.BoundLogger,
    sanic_app: sanic.Sanic[sanic.Config, SimpleNamespace],
    registry: Registry,
) -> sanic.Sanic[sanic.Config, SimpleNamespace]:
    @sanic_app.post("/slack/events", name="slack_events")
    async def slack_events(request: sanic.Request) -> sanic.response.HTTPResponse:
        bolt_resp = await registry.slack_app.async_dispatch(
            bolt_async_handler.to_async_bolt_request(request)
        )
        return bolt_async_handler.to_sanic_response(bolt_resp)

    @sanic_app.post("/github/webhook", name="github_webhook")
    async def github_webhook(request: sanic.Request) -> sanic.response.HTTPResponse:
        return await GithubWebhook(logger, registry.github_webhooks).handle(request)

    return sanic_app
