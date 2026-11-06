from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy.pool import NullPool

from app.users.infrastructure.persistence.models.user_model import UserModel

URL = "/api/v1/users"
SENHA = "S3nha!Forte123"


async def buscar(migrated_database: str, email: str) -> UserModel | None:
    engine = create_async_engine(migrated_database, poolclass=NullPool)
    async with engine.connect() as conn:
        linha = (
            await conn.execute(select(UserModel).where(UserModel.email == email))
        ).first()
    await engine.dispose()
    return None if linha is None else UserModel(**linha._mapping)


async def test_cadastro_grava_no_banco_com_hash_argon2(
    real_client: AsyncClient, fresh_email: str, migrated_database: str
) -> None:
    resposta = await real_client.post(
        URL, json={"email": fresh_email, "password": SENHA}
    )

    assert resposta.status_code == 201
    gravado = await buscar(migrated_database, fresh_email)
    assert gravado is not None
    assert gravado.password_hash.startswith("$argon2id$")
    assert str(gravado.id) == resposta.json()["id"]


async def test_senha_fraca_e_recusada_pelas_regras_em_prolog(
    real_client: AsyncClient, fresh_email: str, migrated_database: str
) -> None:
    resposta = await real_client.post(
        URL, json={"email": fresh_email, "password": "abc"}
    )

    assert resposta.status_code == 422
    assert set(resposta.json()["reasons"]) == {
        "too_short",
        "no_upper",
        "no_digit",
        "no_symbol",
    }
    assert await buscar(migrated_database, fresh_email) is None


async def test_segundo_cadastro_do_mesmo_email_responde_409(
    real_client: AsyncClient, fresh_email: str
) -> None:
    pedido = {"email": fresh_email, "password": SENHA}
    assert (await real_client.post(URL, json=pedido)).status_code == 201

    resposta = await real_client.post(URL, json=pedido)

    assert resposta.status_code == 409
