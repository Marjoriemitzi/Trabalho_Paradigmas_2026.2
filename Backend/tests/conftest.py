import os
from collections.abc import AsyncIterator
from pathlib import Path

import pytest
from alembic import command
from alembic.config import Config
from sqlalchemy.ext.asyncio import (
    AsyncConnection,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.pool import NullPool

BACKEND = Path(__file__).resolve().parents[1]


def pytest_configure() -> None:
    url_de_teste = os.environ.get("TEST_DATABASE_URL")
    if not url_de_teste:
        raise pytest.UsageError(
            "Defina TEST_DATABASE_URL (o docker compose já define no serviço app)."
        )
    if url_de_teste == os.environ.get("DATABASE_URL"):
        raise pytest.UsageError(
            "TEST_DATABASE_URL não pode ser o mesmo banco de DATABASE_URL."
        )
    os.environ["DATABASE_URL"] = url_de_teste


@pytest.fixture(scope="session")
def migrated_database() -> str:
    command.upgrade(Config(str(BACKEND / "alembic.ini")), "head")
    return os.environ["DATABASE_URL"]


@pytest.fixture
async def connection(migrated_database: str) -> AsyncIterator[AsyncConnection]:
    engine = create_async_engine(migrated_database, poolclass=NullPool)
    async with engine.connect() as conn:
        transaction = await conn.begin()
        yield conn
        await transaction.rollback()
    await engine.dispose()


@pytest.fixture
def session_factory(connection: AsyncConnection) -> async_sessionmaker[AsyncSession]:
    return async_sessionmaker(
        bind=connection,
        join_transaction_mode="create_savepoint",
        expire_on_commit=False,
    )


@pytest.fixture
async def session(
    session_factory: async_sessionmaker[AsyncSession],
) -> AsyncIterator[AsyncSession]:
    async with session_factory() as session:
        yield session
