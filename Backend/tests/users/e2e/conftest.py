import uuid
from collections.abc import AsyncIterator

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy import delete
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy.pool import NullPool

from app.main import create_app
from app.users.infrastructure.persistence.models.user_model import UserModel


def ip_do_teste() -> str:
    """Um IP só deste teste, para o limite de tentativas não juntar os testes reais."""
    return "10." + ".".join(str(b) for b in uuid.uuid4().bytes[:3])


@pytest.fixture
async def real_client(migrated_database: str) -> AsyncIterator[AsyncClient]:
    app = create_app()
    async with app.router.lifespan_context(app):
        transport = ASGITransport(app=app, client=(ip_do_teste(), 5000))
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
