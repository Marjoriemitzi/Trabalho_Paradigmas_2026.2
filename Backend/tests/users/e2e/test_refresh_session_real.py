from httpx import AsyncClient
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy.pool import NullPool

from app.users.application.session import hash_refresh_token

SENHA = "S3nha!Forte123"


async def entrar(client: AsyncClient, email: str) -> dict[str, str]:
    pedido = {"email": email, "password": SENHA}
    assert (await client.post("/api/v1/users", json=pedido)).status_code == 201
    resposta = await client.post("/api/v1/auth/login", json=pedido)
    assert resposta.status_code == 200
    return dict(resposta.json())


async def test_login_refresh_reuso_revoga_a_familia_inteira(
    real_client: AsyncClient, fresh_email: str
) -> None:
    login = await entrar(real_client, fresh_email)

    primeiro = await real_client.post(
        "/api/v1/auth/refresh", json={"refresh_token": login["refresh_token"]}
    )
    reuso = await real_client.post(
        "/api/v1/auth/refresh", json={"refresh_token": login["refresh_token"]}
    )
    do_novo = await real_client.post(
        "/api/v1/auth/refresh",
        json={"refresh_token": primeiro.json()["refresh_token"]},
    )

    assert primeiro.status_code == 200
    assert primeiro.json()["refresh_token"] != login["refresh_token"]
    assert reuso.status_code == 401
    assert reuso.json() == {"error": "invalid_refresh_token"}
    assert do_novo.status_code == 401


async def test_o_access_token_novo_da_acesso_a_api(
    real_client: AsyncClient, fresh_email: str
) -> None:
    login = await entrar(real_client, fresh_email)
    renovado = await real_client.post(
        "/api/v1/auth/refresh", json={"refresh_token": login["refresh_token"]}
    )

    eu = await real_client.get(
        "/api/v1/users/me",
        headers={"Authorization": f"Bearer {renovado.json()['access_token']}"},
    )

    assert eu.status_code == 200
    assert eu.json()["email"] == fresh_email


async def test_logout_impede_renovar_e_e_idempotente(
    real_client: AsyncClient, fresh_email: str
) -> None:
    login = await entrar(real_client, fresh_email)

    saida = await real_client.post(
        "/api/v1/auth/logout", json={"refresh_token": login["refresh_token"]}
    )
    repetida = await real_client.post(
        "/api/v1/auth/logout", json={"refresh_token": login["refresh_token"]}
    )
    renovar = await real_client.post(
        "/api/v1/auth/refresh", json={"refresh_token": login["refresh_token"]}
    )

    assert saida.status_code == repetida.status_code == 204
    assert renovar.status_code == 401


async def test_o_banco_so_guarda_o_hash_do_refresh_token(
    real_client: AsyncClient, fresh_email: str, migrated_database: str
) -> None:
    login = await entrar(real_client, fresh_email)

    engine = create_async_engine(migrated_database, poolclass=NullPool)
    async with engine.connect() as conn:
        resultado = await conn.execute(
            text(
                "SELECT rt.token_hash FROM refresh_tokens rt"
                " JOIN users u ON u.id = rt.user_id WHERE u.email = :e"
            ),
            {"e": fresh_email},
        )
        hashes: list[str] = list(resultado.scalars().all())
    await engine.dispose()

    assert hashes == [hash_refresh_token(login["refresh_token"])]
    assert login["refresh_token"] not in hashes


async def test_apagar_o_usuario_apaga_os_refresh_tokens(
    real_client: AsyncClient, fresh_email: str, migrated_database: str
) -> None:
    login = await entrar(real_client, fresh_email)
    await real_client.request(
        "DELETE",
        "/api/v1/users/me",
        json={"password": SENHA},
        headers={"Authorization": f"Bearer {login['access_token']}"},
    )

    engine = create_async_engine(migrated_database, poolclass=NullPool)
    async with engine.connect() as conn:
        restantes = await conn.scalar(
            text("SELECT count(*) FROM refresh_tokens WHERE token_hash = :h"),
            {"h": hash_refresh_token(login["refresh_token"])},
        )
    await engine.dispose()

    assert restantes == 0
