import uuid
from collections.abc import AsyncIterator

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy.pool import NullPool

from app.main import create_app
from app.users.infrastructure.persistence.models.user_model import UserModel

URL = "/api/v1/users"
SENHA = "S3nha!Forte123"


@pytest.fixture
async def client(migrated_database: str) -> AsyncIterator[AsyncClient]:
    app = create_app()
    async with app.router.lifespan_context(app):
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://teste") as client:
            yield client


@pytest.fixture
async def email(migrated_database: str) -> AsyncIterator[str]:
    unico = f"e2e-{uuid.uuid4().hex}@acme.com"
    yield unico
    engine = create_async_engine(migrated_database, poolclass=NullPool)
    async with engine.begin() as conn:
        await conn.execute(delete(UserModel).where(UserModel.email == unico))
    await engine.dispose()


async def buscar(migrated_database: str, email: str) -> UserModel | None:
    engine = create_async_engine(migrated_database, poolclass=NullPool)
    async with engine.connect() as conn:
        linha = (
            await conn.execute(select(UserModel).where(UserModel.email == email))
        ).first()
    await engine.dispose()
    return None if linha is None else UserModel(**linha._mapping)


async def test_cadastro_grava_no_banco_com_hash_argon2(
    client: AsyncClient, email: str, migrated_database: str
) -> None:
    resposta = await client.post(URL, json={"email": email, "password": SENHA})

    assert resposta.status_code == 201
    gravado = await buscar(migrated_database, email)
    assert gravado is not None
    assert gravado.password_hash.startswith("$argon2id$")
    assert str(gravado.id) == resposta.json()["id"]


async def test_senha_fraca_e_recusada_pelas_regras_em_prolog(
    client: AsyncClient, email: str, migrated_database: str
) -> None:
    resposta = await client.post(URL, json={"email": email, "password": "abc"})

    assert resposta.status_code == 422
    assert set(resposta.json()["reasons"]) == {
        "too_short",
        "no_upper",
        "no_digit",
        "no_symbol",
    }
    assert await buscar(migrated_database, email) is None


async def test_segundo_cadastro_do_mesmo_email_responde_409(
    client: AsyncClient, email: str
) -> None:
    pedido = {"email": email, "password": SENHA}
    assert (await client.post(URL, json=pedido)).status_code == 201

    resposta = await client.post(URL, json=pedido)

    assert resposta.status_code == 409
