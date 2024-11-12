from types import SimpleNamespace

import attrs
import sanic
import slack_bolt
from slack_bolt.adapter.sanic import async_handler as sanic_async_handler


@attrs.frozen
class Registry:
    slack_app: slack_bolt.async_app.AsyncApp


def register_sanic_routes(
    sanic_app: sanic.Sanic[sanic.Config, SimpleNamespace], registry: Registry
) -> sanic.Sanic[sanic.Config, SimpleNamespace]:
    @sanic_app.post("/slack/events", name="slack_events")
    async def slack_events(request: sanic.Request) -> sanic.response.HTTPResponse:
        return await sanic_async_handler.AsyncSlackRequestHandler(registry.slack_app).handle(
            request
        )

    return sanic_app
