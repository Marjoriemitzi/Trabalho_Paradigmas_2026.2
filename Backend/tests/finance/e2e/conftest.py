import pytest
from httpx import AsyncClient


@pytest.fixture
async def carteira(real_client: AsyncClient, auth_headers: dict[str, str]) -> str:
    resposta = await real_client.post(
        "/api/v1/accounts",
        json={"name": "Carteira", "kind": "wallet"},
        headers=auth_headers,
    )
    assert resposta.status_code == 201
    return str(resposta.json()["id"])
