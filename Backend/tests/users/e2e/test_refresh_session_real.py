import asyncio

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


async def test_logout_com_o_access_token_bloqueia_o_token_em_todas_as_rotas(
    real_client: AsyncClient, fresh_email: str
) -> None:
    login = await entrar(real_client, fresh_email)
    segunda = await real_client.post(
        "/api/v1/auth/login", json={"email": fresh_email, "password": SENHA}
    )
    revogado = {"Authorization": f"Bearer {login['access_token']}"}
    outro = {"Authorization": f"Bearer {segunda.json()['access_token']}"}

    saida = await real_client.post(
        "/api/v1/auth/logout",
        json={"refresh_token": login["refresh_token"]},
        headers=revogado,
    )

    assert saida.status_code == 204
    for rota in ("/api/v1/users/me", "/api/v1/accounts"):
        resposta = await real_client.get(rota, headers=revogado)
        assert resposta.status_code == 401
        assert resposta.json() == {"error": "invalid_token"}
    assert (await real_client.get("/api/v1/users/me", headers=outro)).status_code == 200


async def test_logout_sem_o_access_token_deixa_ele_valer_ate_vencer(
    real_client: AsyncClient, fresh_email: str
) -> None:
    login = await entrar(real_client, fresh_email)

    await real_client.post(
        "/api/v1/auth/logout", json={"refresh_token": login["refresh_token"]}
    )

    eu = await real_client.get(
        "/api/v1/users/me", headers={"Authorization": f"Bearer {login['access_token']}"}
    )
    assert eu.status_code == 200


async def test_token_sem_jti_nao_entra(
    real_client: AsyncClient, fresh_email: str
) -> None:
    import os
    from datetime import UTC, datetime, timedelta

    import jwt

    login = await entrar(real_client, fresh_email)
    sub = jwt.decode(login["access_token"], options={"verify_signature": False})["sub"]
    agora = datetime.now(UTC)
    antigo = jwt.encode(
        {"sub": sub, "role": "user", "iat": agora, "exp": agora + timedelta(minutes=5)},
        os.environ["JWT_SECRET"],
        algorithm="HS256",
    )

    resposta = await real_client.get(
        "/api/v1/users/me", headers={"Authorization": f"Bearer {antigo}"}
    )

    assert resposta.status_code == 401


async def test_duas_renovacoes_concorrentes_com_mesmo_token_revogam_a_familia(
    real_client: AsyncClient, fresh_email: str, migrated_database: str
) -> None:
    login = await entrar(real_client, fresh_email)
    pedido = {"refresh_token": login["refresh_token"]}

    respostas = await asyncio.gather(
        real_client.post("/api/v1/auth/refresh", json=pedido),
        real_client.post("/api/v1/auth/refresh", json=pedido),
    )

    sucessos = [r for r in respostas if r.status_code == 200]
    recusas = [r for r in respostas if r.status_code == 401]
    assert len(sucessos) <= 1
    assert len(sucessos) + len(recusas) == 2
    for recusa in recusas:
        assert recusa.json() == {"error": "invalid_refresh_token"}

    engine = create_async_engine(migrated_database, poolclass=NullPool)
    async with engine.connect() as conn:
        resultado = await conn.execute(
            text(
                "SELECT rt.revoked_at IS NOT NULL FROM refresh_tokens rt"
                " JOIN users u ON u.id = rt.user_id WHERE u.email = :e"
            ),
            {"e": fresh_email},
        )
        revogados: list[bool] = list(resultado.scalars().all())
    await engine.dispose()
    assert revogados
    assert all(revogados), "a detecção de replay deveria revogar a família inteira"
    for sucesso in sucessos:
        renovar = await real_client.post(
            "/api/v1/auth/refresh",
            json={"refresh_token": sucesso.json()["refresh_token"]},
        )
        assert renovar.status_code == 401
