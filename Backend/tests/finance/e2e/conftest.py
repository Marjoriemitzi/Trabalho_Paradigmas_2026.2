import uuid
from collections.abc import AsyncIterator

import pytest
from httpx import AsyncClient
from sqlalchemy import delete
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy.pool import NullPool

from app.users.infrastructure.persistence.models.user_model import UserModel

SENHA_DO_INTRUSO = "S3nha!Forte123"


@pytest.fixture
async def carteira(real_client: AsyncClient, auth_headers: dict[str, str]) -> str:
    resposta = await real_client.post(
        "/api/v1/accounts",
        json={"name": "Carteira", "kind": "wallet"},
        headers=auth_headers,
    )
    assert resposta.status_code == 201
    return str(resposta.json()["id"])


@pytest.fixture
async def intruso(
    real_client: AsyncClient, migrated_database: str
) -> AsyncIterator[dict[str, str]]:
    """Outro usuário logado; apagado do banco ao fim do teste, mesmo se ele falhar."""
    email = f"intruso-{uuid.uuid4().hex}@acme.com"
    credenciais = {"email": email, "password": SENHA_DO_INTRUSO}
    try:
        criado = await real_client.post("/api/v1/users", json=credenciais)
        assert criado.status_code == 201
        login = await real_client.post("/api/v1/auth/login", json=credenciais)
        assert login.status_code == 200
        yield {"Authorization": f"Bearer {login.json()['access_token']}"}
    finally:
        engine = create_async_engine(migrated_database, poolclass=NullPool)
        try:
            async with engine.begin() as conn:
                await conn.execute(delete(UserModel).where(UserModel.email == email))
        finally:
            await engine.dispose()
