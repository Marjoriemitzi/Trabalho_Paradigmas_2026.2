from datetime import timedelta

from httpx import AsyncClient

from app.users.domain.entities.user import User
from app.users.domain.value_objects.email import Email
from app.users.domain.value_objects.password import PasswordHash
from app.users.infrastructure.security.jwt_token_issuer import JwtTokenIssuer

URL = "/api/v1/users/me"
SENHA = "S3nha!Forte123"


async def entrar(client: AsyncClient, email: str) -> str:
    pedido = {"email": email, "password": SENHA}
    assert (await client.post("/api/v1/users", json=pedido)).status_code == 201
    resposta = await client.post("/api/v1/auth/login", json=pedido)
    assert resposta.status_code == 200
    return str(resposta.json()["access_token"])


async def test_quem_entrou_ve_os_proprios_dados(
    real_client: AsyncClient, fresh_email: str
) -> None:
    token = await entrar(real_client, fresh_email)

    resposta = await real_client.get(URL, headers={"Authorization": f"Bearer {token}"})

    assert resposta.status_code == 200
    assert resposta.json()["email"] == fresh_email


async def test_token_assinado_com_outro_segredo_nao_entra(
    real_client: AsyncClient,
) -> None:
    falsificador = JwtTokenIssuer(
        secret="segredo-de-quem-quer-se-passar-por-outro",
        expires_in=timedelta(minutes=30),
    )
    alguem = User.register(Email("alguem@acme.com"), PasswordHash("hash"))
    forjado = falsificador.issue(alguem).value

    resposta = await real_client.get(
        URL, headers={"Authorization": f"Bearer {forjado}"}
    )

    assert resposta.status_code == 401
