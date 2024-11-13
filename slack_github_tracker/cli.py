import argparse
import asyncio
import os

import sanic
import slack_bolt
from hypercorn.asyncio import serve
from hypercorn.config import Config

from . import events, handlers


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
        "--github-webhook-secret",
        help="The value of the secret for the github webhooks or 'env:NAME_OF_ENV_VAR'",
        default="env:GITHUB_WEBHOOK_SECRET",
        type=_get_secret,
    )

    parser.add_argument(
        "--port",
        help="The port to expose the app from. Defaults to $SLACK_BOT_SERVER_PORT or 3000",
        default=os.environ.get("SLACK_BOT_SERVER_PORT", 3000),
        type=int,
    )

    return parser


def main(argv: list[str] | None = None) -> None:
    parser = make_parser()
    args = parser.parse_args(argv)

    events_handler = events.EventHandler()
    github_webhooks = handlers.github.Hooks(
        secret=args.github_webhook_secret, events=events_handler
    )

    slack_app = slack_bolt.async_app.AsyncApp(
        token=args.slack_bot_token, signing_secret=args.slack_signing_secret
    )
    handlers.slack.register_slack_handlers(slack_app)

    app = sanic.Sanic("slack_github_tracker", env_prefix="SLACK_BOT")
    app.config.MOTD = False

    handlers.server.register_sanic_routes(
        app,
        registry=handlers.server.Registry(slack_app=slack_app, github_webhooks=github_webhooks),
    )

    config = Config()
    config.bind = [f"127.0.0.1:{args.port}"]

    asyncio.run(serve(app, config))
