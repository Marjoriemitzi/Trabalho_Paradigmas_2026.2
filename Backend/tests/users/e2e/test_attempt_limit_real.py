from httpx import AsyncClient

SENHA = "S3nha!Forte123"


async def test_seis_logins_errados_seguidos_o_sexto_da_429_com_retry_after(
    real_client: AsyncClient, fresh_email: str
) -> None:
    await real_client.post(
        "/api/v1/users", json={"email": fresh_email, "password": SENHA}
    )
    pedido = {"email": fresh_email, "password": "errada"}

    for _ in range(5):
        resposta = await real_client.post("/api/v1/auth/login", json=pedido)
        assert resposta.status_code == 401
    sexta = await real_client.post("/api/v1/auth/login", json=pedido)
    certa = await real_client.post(
        "/api/v1/auth/login", json={"email": fresh_email, "password": SENHA}
    )

    assert sexta.status_code == 429
    assert sexta.json() == {"error": "too_many_attempts"}
    assert 0 < int(sexta.headers["retry-after"]) <= 15 * 60
    assert certa.status_code == 429


async def test_o_sexto_cadastro_do_mesmo_ip_da_429(real_client: AsyncClient) -> None:
    codigos = []
    for numero in range(6):
        resposta = await real_client.post(
            "/api/v1/users",
            json={
                "email": f"limite-{numero}-{id(real_client)}@acme.com",
                "password": "x",
            },
        )
        codigos.append(resposta.status_code)

    assert codigos[:5] == [422] * 5
    assert codigos[5] == 429


async def test_login_certo_zera_as_falhas_do_par(
    real_client: AsyncClient, fresh_email: str
) -> None:
    await real_client.post(
        "/api/v1/users", json={"email": fresh_email, "password": SENHA}
    )
    errado = {"email": fresh_email, "password": "errada"}
    for _ in range(4):
        await real_client.post("/api/v1/auth/login", json=errado)

    ok = await real_client.post(
        "/api/v1/auth/login", json={"email": fresh_email, "password": SENHA}
    )
    for _ in range(4):
        resposta = await real_client.post("/api/v1/auth/login", json=errado)
        assert resposta.status_code == 401

    assert ok.status_code == 200
