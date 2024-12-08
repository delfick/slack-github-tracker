from collections.abc import AsyncGenerator

import pytest
import sqlalchemy
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from slack_github_tracker.storage import metadata


def pytest_addoption(parser: pytest.Parser) -> None:
    parser.addoption("--postgres-url", help="url of the database to use for tests", required=True)


@pytest.fixture(scope="session", autouse=True)
async def db_engine(request: pytest.FixtureRequest) -> AsyncGenerator[AsyncEngine]:
    db_url = sqlalchemy.engine.url.make_url(request.config.getoption("--postgres-url"))
    db_url = db_url.set(drivername="postgresql+psycopg")

    engine = create_async_engine(db_url, echo=True)

    async with engine.begin() as conn:
        await conn.run_sync(metadata.drop_all)
        await conn.run_sync(metadata.create_all)

    yield engine

    await engine.dispose()


@pytest.fixture(scope="session")
def db_session_factory(
    db_engine: AsyncEngine,
) -> async_sessionmaker[AsyncSession]:
    return async_sessionmaker(bind=db_engine)


@pytest.fixture
async def db_session(
    db_session_factory: async_sessionmaker[AsyncSession],
) -> AsyncGenerator[AsyncSession]:
    session = db_session_factory()

    yield session

    await session.rollback()
    await session.close()
