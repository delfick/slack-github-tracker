import argparse
import asyncio
import os
import pathlib
import subprocess
import sys

import click
import sqlalchemy
from sqlalchemy.ext.asyncio import create_async_engine

from slack_github_tracker import cli as tracker_cli

here = pathlib.Path(__file__).parent


def run(*args: str, env: dict[str, str] | None = None) -> None:
    try:
        subprocess.run(["/bin/bash", str(here / "uv"), "run", *args], check=True, env=env)
    except subprocess.CalledProcessError as e:
        sys.exit(e.returncode)


@click.group()
def cli() -> None:
    pass


cli.add_command(tracker_cli.main, name="app")


@cli.command(context_settings=dict(ignore_unknown_options=True))
@click.argument("args", nargs=-1, type=click.UNPROCESSED)
def format(args: list[str]) -> None:
    """
    Run ruff format and ruff check fixing I and UP rules
    """
    if not args:
        args = [".", *args]
    subprocess.run([sys.executable, "-m", "ruff", "format", *args], check=True)
    subprocess.run(
        [sys.executable, "-m", "ruff", "check", "--fix", "--select", "I,UP", *args],
        check=True,
    )


@cli.command(context_settings=dict(ignore_unknown_options=True))
@click.argument("args", nargs=-1, type=click.UNPROCESSED)
def lint(args: list[str]) -> None:
    """
    Run ruff check
    """
    os.execv(sys.executable, [sys.executable, "-m", "ruff", "check", *args])


@cli.command(context_settings=dict(ignore_unknown_options=True))
@click.argument("args", nargs=-1, type=click.UNPROCESSED)
def types(args: list[str]) -> None:
    """
    Run mypy
    """
    locations: list[str] = [a for a in args if not a.startswith("-")]
    args = [a for a in args if a.startswith("-")]

    if not locations:
        locations.append(str((here / "..").resolve()))
    else:
        cwd = pathlib.Path.cwd()
        paths: list[pathlib.Path] = []
        for location in locations:
            from_current = cwd / location
            from_root = here.parent / location

            if from_current.exists():
                paths.append(from_current)
            elif from_root.exists():
                paths.append(from_root)
            else:
                raise ValueError(f"Couldn't find path for {location}")

        locations = [str(path) for path in paths]

    run("python", "-m", "mypy", *locations, *args)


@cli.command(context_settings=dict(ignore_unknown_options=True))
@click.argument("args", nargs=-1, type=click.UNPROCESSED)
def tests(args: list[str]) -> None:
    """
    Run pytest
    """
    url_str = "postgresql://localhost/test_slack_github_tracker"
    if "--postgres-url" not in args:
        args = ["--postgres-url", url_str, *args]
    else:
        parser = argparse.ArgumentParser()
        parser.add_argument("--postgres-url")
        url_str = parser.parse_known_args(args)[0].postgres_url

    postgres_url = sqlalchemy.engine.url.make_url(url_str)
    postgres_url = postgres_url.set(drivername="postgresql+psycopg")

    async def ensure_database() -> None:
        engine = create_async_engine(postgres_url)
        try:
            async with engine.connect():
                pass
        except sqlalchemy.exc.OperationalError:
            pass
        else:
            return

        engine = create_async_engine(postgres_url.set(database=""), isolation_level="AUTOCOMMIT")
        async with engine.connect() as connection:
            await connection.execute(sqlalchemy.text(f"CREATE DATABASE {postgres_url.database}"))

        await engine.dispose()

    asyncio.run(ensure_database())

    run("python", "-m", "pytest", *args)


@cli.command(context_settings=dict(ignore_unknown_options=True))
@click.argument("args", nargs=-1, type=click.UNPROCESSED)
def alembic(args: list[str]) -> None:
    """
    Run alembic
    """
    alembic_db_url = "postgresql://localhost/slack-github-tracker"
    run("python", "-m", "alembic", *args, env={**os.environ, "ALEMBIC_DB_URL": alembic_db_url})


if __name__ == "__main__":
    cli()
