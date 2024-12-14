import functools
import logging
import os
from collections.abc import Callable
from typing import Any

import click
import structlog

from . import http_server, protocols


class EnvSecret(click.ParamType):
    name = "env_secret"

    def convert(self, value: Any, param: click.Parameter | None, ctx: click.Context | None) -> str:
        if not isinstance(value, str):
            self.fail("Expect env value to be a str", param, ctx)
        if value.startswith("env:"):
            env_name = value[4:]
            from_env = os.environ.get(env_name)
            if from_env is None:
                raise self.fail(f"No value found for environment variable ${env_name}", param, ctx)
            value = from_env
        return value


def setup_logging(dev_logging: bool) -> protocols.Logger:
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


def start_http_server(
    *,
    slack_bot_token: str,
    slack_signing_secret: str,
    github_webhook_secret: str,
    postgres_url: str,
    port: int,
    dev_logging: bool,
    server_kls: type[http_server.Server],
) -> None:
    logger = setup_logging(dev_logging)
    server = server_kls(
        postgres_url=postgres_url,
        slack_bot_token=slack_bot_token,
        slack_signing_secret=slack_signing_secret,
        github_webhook_secret=github_webhook_secret,
        port=port,
        logger=logger,
    )
    server.serve_forever()


def http_server_args[**P_Args, T_Ret](func: Callable[P_Args, T_Ret]) -> Callable[P_Args, T_Ret]:
    @click.option(
        "--slack-bot-token",
        help="The value of the token for the slack bot or 'env:NAME_OF_ENV_VAR'",
        default="env:SLACK_BOT_TOKEN",
        type=EnvSecret(),
    )
    @click.option(
        "--slack-signing-secret",
        help="The value of the signing secret for the slack app or 'env:NAME_OF_ENV_VAR'",
        default="env:SLACK_SIGNING_SECRET",
        type=EnvSecret(),
    )
    @click.option(
        "--github-webhook-secret",
        help="The value of the secret for the github webhooks or 'env:NAME_OF_ENV_VAR'",
        default="env:GITHUB_WEBHOOK_SECRET",
        type=EnvSecret(),
    )
    @click.option(
        "--postgres-url",
        help="The url for the postgres database",
        default="env:ALEMBIC_DB_URL",
        type=EnvSecret(),
    )
    @click.option(
        "--port",
        help="The port to expose the app from. Defaults to $SLACK_BOT_SERVER_PORT or 3000",
        default=os.environ.get("SLACK_BOT_SERVER_PORT", 3000),
        type=int,
    )
    @click.option(
        "--dev-logging",
        is_flag=True,
        help="Print out the logs as human readable",
    )
    @functools.wraps(func)
    def wrapped(*args: P_Args.args, **kwargs: P_Args.kwargs) -> T_Ret:
        return func(*args, **kwargs)

    return wrapped


@click.command
@http_server_args
def serve_http(
    *,
    slack_bot_token: str,
    slack_signing_secret: str,
    github_webhook_secret: str,
    postgres_url: str,
    port: int,
    dev_logging: bool,
) -> None:
    return start_http_server(
        slack_bot_token=slack_bot_token,
        slack_signing_secret=slack_signing_secret,
        github_webhook_secret=github_webhook_secret,
        postgres_url=postgres_url,
        port=port,
        dev_logging=dev_logging,
        server_kls=http_server.Server,
    )


@click.group(help="Interact with slack github tracker")
def main() -> None:
    pass


main.add_command(serve_http)
