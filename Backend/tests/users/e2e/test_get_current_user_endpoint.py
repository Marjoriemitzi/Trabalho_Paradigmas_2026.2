from collections.abc import AsyncIterator

import pytest
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient

from app.users.application.use_cases.get_current_user import (
    GetCurrentUserInputPort,
    GetCurrentUserInteractor,
    GetCurrentUserOutputPort,
)
from app.users.domain.entities.user import User
from app.users.domain.value_objects.email import Email
from app.users.domain.value_objects.password import PasswordHash
from app.users.presentation.api.v1.routers.users import router
from tests.users.fakes.fake_token_issuer import FakeTokenIssuer
from tests.users.fakes.fake_token_verifier import FakeTokenVerifier
from tests.users.fakes.fake_unit_of_work import FakeUnitOfWork

URL = "/api/v1/users/me"
ANA = User.register(Email("ana@acme.com"), PasswordHash("hash"))


def bearer(user: User) -> dict[str, str]:
    token = FakeTokenIssuer().issue(user).value
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
async def client() -> AsyncIterator[AsyncClient]:
    uow = FakeUnitOfWork()
    await uow.users.add(ANA)

    def build_interactor(
        presenter: GetCurrentUserOutputPort,
    ) -> GetCurrentUserInputPort:
        return GetCurrentUserInteractor(uow=uow, presenter=presenter)

    app = FastAPI()
    app.include_router(router)
    app.state.get_current_user = build_interactor
    app.state.token_verifier = FakeTokenVerifier()

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://teste") as client:
        yield client


async def test_com_token_valido_responde_200_com_os_dados(client: AsyncClient) -> None:
    resposta = await client.get(URL, headers=bearer(ANA))

    assert resposta.status_code == 200
    assert resposta.json() == {
        "id": str(ANA.id.value),
        "email": "ana@acme.com",
        "role": "user",
    }


async def test_sem_token_responde_401(client: AsyncClient) -> None:
    resposta = await client.get(URL)

    assert resposta.status_code == 401
    assert resposta.json() == {"detail": "not_authenticated"}
    assert resposta.headers["www-authenticate"] == "Bearer"


async def test_token_invalido_responde_401(client: AsyncClient) -> None:
    resposta = await client.get(URL, headers={"Authorization": "Bearer abc.def.ghi"})

    assert resposta.status_code == 401
    assert resposta.json() == {"detail": "invalid_token"}
    assert resposta.headers["www-authenticate"] == 'Bearer error="invalid_token"'


async def test_outro_esquema_de_autenticacao_conta_como_sem_token(
    client: AsyncClient,
) -> None:
    resposta = await client.get(URL, headers={"Authorization": "Basic YW5hOnNlbmhh"})

    assert resposta.status_code == 401
    assert resposta.json() == {"detail": "not_authenticated"}


async def test_token_de_conta_que_nao_existe_mais_responde_401(
    client: AsyncClient,
) -> None:
    sumiu = User.register(Email("bia@acme.com"), PasswordHash("hash"))

    resposta = await client.get(URL, headers=bearer(sumiu))

    assert resposta.status_code == 401
    assert resposta.json() == {"detail": "invalid_token"}
    assert resposta.headers["www-authenticate"] == 'Bearer error="invalid_token"'


def test_a_documentacao_mostra_que_a_rota_exige_token() -> None:
    app = FastAPI()
    app.include_router(router)

    operacao = app.openapi()["paths"][URL]["get"]

    assert operacao["security"] == [{"HTTPBearer": []}]
    assert {"200", "401"} <= set(operacao["responses"])
