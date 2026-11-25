from httpx import AsyncClient

URL = "/api/v1/users/me/password"
ATUAL = "S3nha!Forte123"
NOVA = "N0va!SenhaForte"


async def test_trocar_a_senha_de_ponta_a_ponta(
    real_client: AsyncClient, auth_headers: dict[str, str], fresh_email: str
) -> None:
    resposta = await real_client.post(
        URL,
        json={"current_password": ATUAL, "new_password": NOVA},
        headers=auth_headers,
    )

    antiga = await real_client.post(
        "/api/v1/auth/login", json={"email": fresh_email, "password": ATUAL}
    )
    nova = await real_client.post(
        "/api/v1/auth/login", json={"email": fresh_email, "password": NOVA}
    )
    assert resposta.status_code == 204
    assert antiga.status_code == 401
    assert antiga.json() == {"error": "invalid_credentials"}
    assert nova.status_code == 200


async def test_senha_atual_errada_nao_troca_nada(
    real_client: AsyncClient, auth_headers: dict[str, str], fresh_email: str
) -> None:
    resposta = await real_client.post(
        URL,
        json={"current_password": "errada", "new_password": NOVA},
        headers=auth_headers,
    )

    login = await real_client.post(
        "/api/v1/auth/login", json={"email": fresh_email, "password": ATUAL}
    )
    assert resposta.status_code == 422
    assert resposta.json() == {"error": "invalid_current_password"}
    assert login.status_code == 200


async def test_senha_nova_fraca_e_recusada_com_os_motivos(
    real_client: AsyncClient, auth_headers: dict[str, str]
) -> None:
    resposta = await real_client.post(
        URL,
        json={"current_password": ATUAL, "new_password": "abc"},
        headers=auth_headers,
    )

    assert resposta.status_code == 422
    assert resposta.json()["error"] == "weak_password"
    assert "too_short" in resposta.json()["reasons"]


async def test_trocar_a_senha_revoga_os_refresh_tokens_de_todas_as_sessoes(
    real_client: AsyncClient, auth_headers: dict[str, str], fresh_email: str
) -> None:
    credenciais = {"email": fresh_email, "password": ATUAL}
    sessoes = [
        (await real_client.post("/api/v1/auth/login", json=credenciais)).json()
        for _ in range(2)
    ]

    troca = await real_client.post(
        URL,
        json={"current_password": ATUAL, "new_password": NOVA},
        headers=auth_headers,
    )

    assert troca.status_code == 204
    for sessao in sessoes:
        renovacao = await real_client.post(
            "/api/v1/auth/refresh", json={"refresh_token": sessao["refresh_token"]}
        )
        assert renovacao.status_code == 401
        assert renovacao.json() == {"error": "invalid_refresh_token"}
