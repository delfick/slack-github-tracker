import argparse
import asyncio
import logging
import os

import sanic
import slack_bolt
import structlog
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

    parser.add_argument(
        "--dev-logging",
        help="Print out the logs as human readable",
        action="store_true",
    )

    return parser


def setup_logging(dev_logging: bool) -> structlog.stdlib.BoundLogger:
    timestamper = structlog.processors.TimeStamper(fmt="%Y-%m-%d %H:%M:%S")
    shared_processors: list[structlog.typing.Processor] = [
        # structlog.contextvars.merge_contextvars,
        structlog.stdlib.add_log_level,
        # structlog.processors.StackInfoRenderer(),
        timestamper,
    ]

    structlog.configure(
        processors=[
            *shared_processors,
            structlog.stdlib.ProcessorFormatter.wrap_for_formatter,
        ],
        wrapper_class=structlog.stdlib.BoundLogger,
        logger_factory=structlog.stdlib.LoggerFactory(),
        cache_logger_on_first_use=True,
    )

    log = structlog.get_logger().bind()
    assert isinstance(log, structlog.stdlib.BoundLogger)

    # And make stdlib logging use structlog
    formatter = structlog.stdlib.ProcessorFormatter(
        foreign_pre_chain=shared_processors,
        processors=[
            structlog.stdlib.ProcessorFormatter.remove_processors_meta,
            *(
                (
                    structlog.dev.set_exc_info,
                    structlog.dev.ConsoleRenderer(),
                )
                if dev_logging
                else (structlog.processors.JSONRenderer(),)
            ),
        ],
    )
    handler = logging.StreamHandler()
    handler.setFormatter(formatter)

    root_logger = logging.getLogger()
    root_logger.propagate = False
    root_logger.addHandler(handler)
    root_logger.setLevel(logging.INFO)

    return log


def main(argv: list[str] | None = None) -> None:
    parser = make_parser()
    args = parser.parse_args(argv)

    config = Config()
    config.accesslog = logging.getLogger("hypercorn.access")
    config.errorlog = logging.getLogger("hypercorn.access")
    config.bind = [f"127.0.0.1:{args.port}"]

    logger = setup_logging(args.dev_logging)

    events_handler = events.EventHandler(logger=logger)
    github_webhooks = handlers.github.Hooks(
        logger=logger, secret=args.github_webhook_secret, events=events_handler
    )

    slack_app = slack_bolt.async_app.AsyncApp(
        token=args.slack_bot_token, signing_secret=args.slack_signing_secret
    )
    handlers.slack.register_slack_handlers(
        deps=handlers.slack.Deps(logger=logger),
        app=slack_app,
    )

    app = sanic.Sanic("slack_github_tracker", env_prefix="SLACK_BOT", configure_logging=False)
    app.config.MOTD = False

    handlers.server.register_sanic_routes(
        logger=logger,
        sanic_app=app,
        registry=handlers.server.Registry(slack_app=slack_app, github_webhooks=github_webhooks),
    )

    asyncio.run(serve(app, config))
