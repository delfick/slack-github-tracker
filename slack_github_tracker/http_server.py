import abc
import asyncio
import logging
import signal
from types import SimpleNamespace

import attrs
import sanic
import slack_bolt
import sqlalchemy
from hypercorn.asyncio import serve as hypercorn_serve
from hypercorn.config import Config
from machinery import helpers as hp
from sqlalchemy.ext.asyncio import create_async_engine

from . import handlers, protocols


@attrs.frozen
class ServerBase[T_SanicConfig: sanic.Config, T_SanicNamespace, T_HypercornConfig: Config]:
    postgres_url: str
    slack_bot_token: str
    slack_signing_secret: str
    github_webhook_secret: str
    port: int
    logger: protocols.Logger
    graceful_timeout_seconds: int = 600

    def serve_forever(self) -> None:
        config = self.make_hypercorn_config()
        config = self.configure_hypercorn_config(config)

        database = self.make_database()
        background_tasks = self.make_background_tasks()
        events_handler = self.make_events_handler()

        github_event_interpreter = self.make_github_event_interpreter(
            database=database, background_tasks=background_tasks
        )
        github_webhooks = self.make_github_webhooks(
            events_handler=events_handler, github_event_interpreter=github_event_interpreter
        )

        slack_app = self.make_slack_app()
        slack_app = self.configure_slack_app(
            slack_app=slack_app,
            database=database,
            github_webhooks=github_webhooks,
            background_tasks=background_tasks,
        )

        app = self.make_sanic_app()
        app = self.configure_sanic(
            app=app,
            slack_app=slack_app,
            database=database,
            github_webhooks=github_webhooks,
            background_tasks=background_tasks,
        )

        self.configure_events_handler(
            events_handler=events_handler,
            app=app,
            slack_app=slack_app,
            database=database,
            github_webhooks=github_webhooks,
            background_tasks=background_tasks,
        )

        asyncio.run(self.serve_app(app=app, config=config, background_tasks=background_tasks))

    def make_slack_app(self) -> slack_bolt.async_app.AsyncApp:
        return slack_bolt.async_app.AsyncApp(
            token=self.slack_bot_token, signing_secret=self.slack_signing_secret
        )

    @abc.abstractmethod
    def make_sanic_app(self) -> sanic.Sanic[T_SanicConfig, T_SanicNamespace]: ...

    @abc.abstractmethod
    def make_hypercorn_config(self) -> T_HypercornConfig: ...

    def make_database(self) -> sqlalchemy.ext.asyncio.AsyncEngine:
        postgres_url = sqlalchemy.engine.url.make_url(self.postgres_url)
        postgres_url = postgres_url.set(drivername="postgresql+psycopg")
        return create_async_engine(postgres_url)

    def make_background_tasks(self) -> handlers.background.tasks.Tasks:
        return handlers.background.tasks.Tasks(logger=self.logger)

    def make_github_event_interpreter(
        self,
        *,
        database: sqlalchemy.ext.asyncio.AsyncEngine,
        background_tasks: handlers.background.protocols.TasksAdder,
    ) -> handlers.github.protocols.EventInterpreter:
        return handlers.github.interpret.EventInterpreter()

    def make_events_handler(self) -> handlers.github.handler.EventHandler:
        return handlers.github.handler.EventHandler(logger=self.logger)

    def make_github_webhooks(
        self,
        *,
        events_handler: handlers.github.protocols.EventHandler,
        github_event_interpreter: handlers.github.protocols.EventInterpreter,
    ) -> handlers.github.hooks.Hooks:
        return handlers.github.hooks.Hooks(
            logger=self.logger,
            secret=self.github_webhook_secret,
            event_adder=events_handler,
            event_interpreter=github_event_interpreter,
        )

    def configure_hypercorn_config(self, config: T_HypercornConfig) -> T_HypercornConfig:
        config.accesslog = logging.getLogger("hypercorn.access")
        config.errorlog = logging.getLogger("hypercorn.access")
        config.bind = [f"127.0.0.1:{self.port}"]
        return config

    def configure_slack_app(
        self,
        *,
        slack_app: slack_bolt.async_app.AsyncApp,
        database: sqlalchemy.ext.asyncio.AsyncEngine,
        background_tasks: handlers.background.protocols.TasksAdder,
        github_webhooks: handlers.github.hooks.Hooks,
    ) -> slack_bolt.async_app.AsyncApp:
        handlers.slack.register_slack_handlers(
            deps=handlers.slack.Deps(logger=self.logger, database=database),
            app=slack_app,
        )
        return slack_app

    def configure_sanic(
        self,
        *,
        app: sanic.Sanic[T_SanicConfig, T_SanicNamespace],
        slack_app: slack_bolt.async_app.AsyncApp,
        database: sqlalchemy.ext.asyncio.AsyncEngine,
        background_tasks: handlers.background.protocols.TasksAdder,
        github_webhooks: handlers.github.hooks.Hooks,
    ) -> sanic.Sanic[T_SanicConfig, T_SanicNamespace]:
        handlers.server.register_sanic_routes(
            logger=self.logger,
            sanic_app=app,
            registry=handlers.server.Registry(
                slack_app=slack_app, github_webhooks=github_webhooks
            ),
        )
        return app

    def configure_events_handler(
        self,
        *,
        events_handler: handlers.github.handler.EventHandler,
        app: sanic.Sanic[T_SanicConfig, T_SanicNamespace],
        slack_app: slack_bolt.async_app.AsyncApp,
        database: sqlalchemy.ext.asyncio.AsyncEngine,
        background_tasks: handlers.background.protocols.TasksAdder,
        github_webhooks: handlers.github.hooks.Hooks,
    ) -> None:
        def run_events_handler(
            final_future: asyncio.Future[None], task_holder: hp.TaskHolder
        ) -> None:
            task_holder.add(
                events_handler.run(
                    final_future=final_future,
                    task_holder=task_holder,
                    database=database,
                    background_tasks=background_tasks,
                    slack_app=slack_app,
                )
            )

        background_tasks.append(run_events_handler)

    async def serve_app(
        self,
        *,
        app: sanic.Sanic[T_SanicConfig, T_SanicNamespace],
        config: T_HypercornConfig,
        background_tasks: handlers.background.tasks.Tasks,
    ) -> None:
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

            try:
                await hypercorn_serve(app, config, shutdown_trigger=shutdown_event.wait)
            finally:
                runner.final_fut.cancel()

        if graceful_handle is not None:
            graceful_handle.cancel()


@attrs.frozen
class Server(ServerBase[sanic.Config, SimpleNamespace, Config]):
    def make_sanic_app(self) -> sanic.Sanic[sanic.Config, SimpleNamespace]:
        app = sanic.Sanic("slack_github_tracker", env_prefix="SLACK_BOT", configure_logging=False)
        app.config.MOTD = False
        return app

    def make_hypercorn_config(self) -> Config:
        return Config()
