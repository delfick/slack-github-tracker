import asyncio
import logging

import attrs
import sanic
import slack_bolt
from hypercorn.asyncio import serve as hypercorn_serve
from hypercorn.config import Config

from . import events, handlers, protocols


@attrs.frozen
class Server:
    slack_bot_token: str
    slack_signing_secret: str
    github_webhook_secret: str
    port: int
    logger: protocols.Logger

    def serve_forever(self) -> None:
        config = Config()
        config.accesslog = logging.getLogger("hypercorn.access")
        config.errorlog = logging.getLogger("hypercorn.access")
        config.bind = [f"127.0.0.1:{self.port}"]

        events_handler = events.EventHandler(logger=self.logger)
        github_webhooks = handlers.github.Hooks(
            logger=self.logger, secret=self.github_webhook_secret, events=events_handler
        )

        slack_app = slack_bolt.async_app.AsyncApp(
            token=self.slack_bot_token, signing_secret=self.slack_signing_secret
        )
        handlers.slack.register_slack_handlers(
            deps=handlers.slack.Deps(logger=self.logger),
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

        asyncio.run(hypercorn_serve(app, config))
