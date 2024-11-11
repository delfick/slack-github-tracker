import argparse
import asyncio
import os
from types import SimpleNamespace

import sanic
import slack_bolt
from hypercorn.asyncio import serve
from hypercorn.config import Config
from slack_bolt.adapter.sanic import async_handler as sanic_async_handler

from . import _handlers as handlers


def _get_secret(val: str) -> str:
    if val.startswith("env:"):
        env_name = val[4:]
        from_env = os.environ.get(env_name)
        if from_env is None:
            raise argparse.ArgumentError(
                None, f"No value found for environment variable ${env_name}"
            )
        val = from_env
    return val


def make_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--slack-bot-token",
        help="The value of the token for the slack bot or 'env:NAME_OF_ENV_VAR'",
        default="env:SLACK_BOT_TOKEN",
        type=_get_secret,
    )

    parser.add_argument(
        "--slack-signing-secret",
        help="The value of the signing secret for the slack app or 'env:NAME_OF_ENV_VAR'",
        default="env:SLACK_SIGNING_SECRET",
        type=_get_secret,
    )

    parser.add_argument(
        "--port",
        help="The port to expose the app from. Defaults to $SLACK_BOT_SERVER_PORT or 3000",
        default=os.environ.get("SLACK_BOT_SERVER_PORT", 3000),
        type=int,
    )

    return parser


def register_sanic_routes(
    sanic_app: sanic.Sanic[sanic.Config, SimpleNamespace], slack_app: slack_bolt.async_app.AsyncApp
) -> sanic.Sanic[sanic.Config, SimpleNamespace]:
    @sanic_app.post("/slack/events", name="slack_events")
    async def slack_events(request: sanic.Request) -> sanic.response.HTTPResponse:
        return await sanic_async_handler.AsyncSlackRequestHandler(slack_app).handle(request)

    return sanic_app


def main(argv: list[str] | None = None) -> None:
    parser = make_parser()
    args = parser.parse_args(argv)

    slack_app = slack_bolt.async_app.AsyncApp(
        token=args.slack_bot_token, signing_secret=args.slack_signing_secret
    )
    handlers.register_handlers(slack_app)

    app = sanic.Sanic("slack_github_tracker", env_prefix="SLACK_BOT")
    register_sanic_routes(app, slack_app)

    config = Config()
    config.bind = [f"127.0.0.1:{args.port}"]

    asyncio.run(serve(app, config))
