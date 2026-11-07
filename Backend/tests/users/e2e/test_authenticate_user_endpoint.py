from collections.abc import AsyncIterator

import pytest
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient

from app.shared.presentation.api.error_handlers import install_error_handlers
from app.users.application.use_cases.authenticate_user import (
    AuthenticateUserInputPort,
    AuthenticateUserInteractor,
    AuthenticateUserOutputPort,
)
from app.users.domain.entities.user import User
from app.users.domain.value_objects.email import Email
from app.users.domain.value_objects.password import PasswordHash
from app.users.presentation.api.v1.routers.auth import router
from tests.users.fakes.fake_password_hasher import FakePasswordHasher
from tests.users.fakes.fake_token_issuer import FakeTokenIssuer
from tests.users.fakes.fake_unit_of_work import FakeUnitOfWork

URL = "/api/v1/auth/login"
SENHA = "S3nha!Forte123"


@pytest.fixture
async def client() -> AsyncIterator[AsyncClient]:
    uow = FakeUnitOfWork()
    ana = User.register(Email("ana@acme.com"), PasswordHash(f"hash-falso:{SENHA}"))
    await uow.users.add(ana)

    def build_interactor(
        presenter: AuthenticateUserOutputPort,
    ) -> AuthenticateUserInputPort:
        return AuthenticateUserInteractor(
            uow=uow,
            hasher=FakePasswordHasher(),
            tokens=FakeTokenIssuer(),
            presenter=presenter,
        )

    app = FastAPI()
    install_error_handlers(app)
    app.include_router(router)

    app.state.authenticate_user = build_interactor

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://teste") as client:
        yield client


async def test_login_certo_responde_200_com_token(client: AsyncClient) -> None:
    resposta = await client.post(URL, json={"email": "ana@acme.com", "password": SENHA})

    assert resposta.status_code == 200
    assert resposta.json()["token_type"] == "bearer"
    assert resposta.json()["access_token"].startswith("token-falso:")
    assert resposta.headers["cache-control"] == "no-store"


async def test_senha_errada_e_email_desconhecido_respondem_igual(
    client: AsyncClient,
) -> None:
    senha_errada = await client.post(
        URL, json={"email": "ana@acme.com", "password": "errada"}
    )
    sem_conta = await client.post(
        URL, json={"email": "bia@acme.com", "password": SENHA}
    )

    for resposta in (senha_errada, sem_conta):
        assert resposta.status_code == 401
        assert resposta.json() == {"error": "invalid_credentials"}
        assert resposta.headers["www-authenticate"] == "Bearer"


async def test_campo_a_mais_no_pedido_e_recusado(client: AsyncClient) -> None:
    resposta = await client.post(
        URL, json={"email": "ana@acme.com", "password": SENHA, "remember": True}
    )

    assert resposta.status_code == 422
    assert resposta.json() == {
        "error": "invalid_request",
        "fields": [{"field": "remember", "problem": "extra_forbidden"}],
    }


def test_a_documentacao_mostra_o_401() -> None:
    app = FastAPI()
    app.include_router(router)

    respostas = app.openapi()["paths"][URL]["post"]["responses"]

    assert {"200", "401"} <= set(respostas)
