import argparse
import os

from slack_bolt import App


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
        help="The port to expose the app from. Defaults to $SLACK_BOT_PORT or 3000",
        default=os.environ.get("SLACK_BOT_PORT", 3000),
        type=int,
    )

    return parser


def main(argv: list[str] | None = None) -> None:
    parser = make_parser()
    args = parser.parse_args(argv)

    app = App(token=args.slack_bot_token, signing_secret=args.slack_signing_secret)

    try:
        print(f"⚡️ Running server on http://127.0.0.1:{args.port}/slack/events")  # noqa:T201
        app.start(port=args.port)
    except KeyboardInterrupt:
        pass
