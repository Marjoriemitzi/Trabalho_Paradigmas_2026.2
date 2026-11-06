import os

import jwt
from httpx import AsyncClient

SENHA = "S3nha!Forte123"


async def cadastrar(client: AsyncClient, email: str) -> str:
    resposta = await client.post(
        "/api/v1/users", json={"email": email, "password": SENHA}
    )
    assert resposta.status_code == 201
    return str(resposta.json()["id"])


async def test_quem_se_cadastrou_consegue_entrar(
    real_client: AsyncClient, fresh_email: str
) -> None:
    user_id = await cadastrar(real_client, fresh_email)

    resposta = await real_client.post(
        "/api/v1/auth/login", json={"email": fresh_email, "password": SENHA}
    )

    assert resposta.status_code == 200
    token = resposta.json()["access_token"]
    claims = jwt.decode(token, os.environ["JWT_SECRET"], algorithms=["HS256"])
    assert claims["sub"] == user_id
    assert claims["role"] == "user"


async def test_senha_errada_nao_entra(
    real_client: AsyncClient, fresh_email: str
) -> None:
    await cadastrar(real_client, fresh_email)

    resposta = await real_client.post(
        "/api/v1/auth/login", json={"email": fresh_email, "password": "errada"}
    )

    assert resposta.status_code == 401
