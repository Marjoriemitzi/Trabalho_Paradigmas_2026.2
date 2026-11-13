import os
import uuid
from collections.abc import AsyncIterator
from pathlib import Path

import pytest
from alembic import command
from alembic.config import Config
from httpx import ASGITransport, AsyncClient
from sqlalchemy import delete
from sqlalchemy.ext.asyncio import (
    AsyncConnection,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.pool import NullPool

from app.main import create_app
from app.users.infrastructure.persistence.models.user_model import UserModel

BACKEND = Path(__file__).resolve().parents[1]

pytest.register_assert_rewrite("tests.users.contracts", "tests.finance.contracts")


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


@pytest.fixture
async def real_client(migrated_database: str) -> AsyncIterator[AsyncClient]:
    app = create_app()
    async with app.router.lifespan_context(app):
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://teste") as client:
            yield client


@pytest.fixture
async def fresh_email(migrated_database: str) -> AsyncIterator[str]:
    unico = f"e2e-{uuid.uuid4().hex}@acme.com"
    yield unico
    engine = create_async_engine(migrated_database, poolclass=NullPool)
    async with engine.begin() as conn:
        await conn.execute(delete(UserModel).where(UserModel.email == unico))
    await engine.dispose()


@pytest.fixture
async def auth_headers(real_client: AsyncClient, fresh_email: str) -> dict[str, str]:
    pedido = {"email": fresh_email, "password": "S3nha!Forte123"}
    assert (await real_client.post("/api/v1/users", json=pedido)).status_code == 201
    resposta = await real_client.post("/api/v1/auth/login", json=pedido)
    assert resposta.status_code == 200
    return {"Authorization": f"Bearer {resposta.json()['access_token']}"}
