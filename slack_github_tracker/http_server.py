import asyncio
import logging
import signal

import attrs
import sanic
import slack_bolt
import sqlalchemy
from hypercorn.asyncio import serve as hypercorn_serve
from hypercorn.config import Config
from sqlalchemy.ext.asyncio import create_async_engine

from . import events, handlers, protocols


@attrs.frozen
class Server:
    postgres_url: str
    slack_bot_token: str
    slack_signing_secret: str
    github_webhook_secret: str
    port: int
    logger: protocols.Logger
    graceful_timeout_seconds: int = 600

    def serve_forever(self) -> None:
        config = Config()
        config.accesslog = logging.getLogger("hypercorn.access")
        config.errorlog = logging.getLogger("hypercorn.access")
        config.bind = [f"127.0.0.1:{self.port}"]

        postgres_url = sqlalchemy.engine.url.make_url(self.postgres_url)
        postgres_url = postgres_url.set(drivername="postgresql+psycopg")
        database = create_async_engine(postgres_url)

        background_tasks = handlers.background.tasks.Tasks(logger=self.logger)

        events_handler = events.EventHandler(logger=self.logger)
        github_webhooks = handlers.github.Hooks(
            logger=self.logger, secret=self.github_webhook_secret, events=events_handler
        )

        slack_app = slack_bolt.async_app.AsyncApp(
            token=self.slack_bot_token, signing_secret=self.slack_signing_secret
        )
        handlers.slack.register_slack_handlers(
            deps=handlers.slack.Deps(logger=self.logger, database=database),
            app=slack_app,
        )

        app = sanic.Sanic("slack_github_tracker", env_prefix="SLACK_BOT", configure_logging=False)
        app.config.MOTD = False

        handlers.server.register_sanic_routes(
            logger=self.logger,
            sanic_app=app,
            registry=handlers.server.Registry(
                slack_app=slack_app, github_webhooks=github_webhooks
            ),
        )

        async def serve() -> None:
            graceful_handle: asyncio.Handle | None = None
            async with background_tasks.runner() as runner:
                shutdown_event = asyncio.Event()

                def on_sigterm() -> None:
                    nonlocal graceful_handle
                    graceful_handle = asyncio.get_running_loop().call_later(
                        self.graceful_timeout_seconds, runner.final_fut.cancel
                    )
                    shutdown_event.set()

                asyncio.get_running_loop().add_signal_handler(signal.SIGINT, on_sigterm)
                asyncio.get_running_loop().add_signal_handler(signal.SIGTERM, on_sigterm)

                await hypercorn_serve(app, config, shutdown_trigger=shutdown_event.wait)
                runner.final_fut.cancel()

            if graceful_handle is not None:
                graceful_handle.cancel()

        asyncio.run(serve())
