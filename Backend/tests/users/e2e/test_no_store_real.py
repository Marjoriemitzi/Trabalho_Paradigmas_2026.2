from httpx import AsyncClient


async def test_respostas_com_dado_pessoal_levam_no_store(
    real_client: AsyncClient, auth_headers: dict[str, str], fresh_email: str
) -> None:
    conta = await real_client.post(
        "/api/v1/accounts",
        json={"name": "Cache", "kind": "checking"},
        headers=auth_headers,
    )
    eu = await real_client.get("/api/v1/users/me", headers=auth_headers)
    cadastro = await real_client.post(
        "/api/v1/users",
        json={"email": f"outro-{fresh_email}", "password": "S3nha!Forte123"},
    )

    assert conta.headers["cache-control"] == "no-store"
    assert eu.headers["cache-control"] == "no-store"
    assert cadastro.headers["cache-control"] == "no-store"
