from collections.abc import AsyncIterator

import pytest
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient

from app.shared.presentation.api.error_handlers import install_error_handlers
from app.users.application.use_cases.delete_user import (
    DeleteUserInputPort,
    DeleteUserInteractor,
    DeleteUserOutputPort,
)
from app.users.domain.entities.user import User
from app.users.domain.value_objects.email import Email
from app.users.domain.value_objects.password import PasswordHash
from app.users.presentation.api.v1.routers.users import router
from tests.users.fakes.fake_access_token_check import FakeAccessTokenCheck
from tests.users.fakes.fake_password_hasher import FakePasswordHasher
from tests.users.fakes.fake_token_issuer import FakeTokenIssuer
from tests.users.fakes.fake_token_verifier import FakeTokenVerifier
from tests.users.fakes.fake_unit_of_work import FakeUnitOfWork

URL = "/api/v1/users/me"
SENHA = "S3nha!Forte123"


def bearer(user: User) -> dict[str, str]:
    return {"Authorization": f"Bearer {FakeTokenIssuer().issue(user).value}"}


@pytest.fixture
async def ana() -> User:
    return User.register(Email("ana@acme.com"), PasswordHash(f"hash-falso:{SENHA}"))


@pytest.fixture
async def client(ana: User) -> AsyncIterator[AsyncClient]:
    uow = FakeUnitOfWork()
    await uow.users.add(ana)

    def build_interactor(presenter: DeleteUserOutputPort) -> DeleteUserInputPort:
        return DeleteUserInteractor(
            uow=uow, hasher=FakePasswordHasher(), presenter=presenter
        )

    app = FastAPI()
    install_error_handlers(app)
    app.include_router(router)
    app.state.delete_user = build_interactor
    app.state.token_verifier = FakeTokenVerifier()
    app.state.access_token_check = FakeAccessTokenCheck(uow.users)

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://teste") as client:
        yield client


async def test_com_a_senha_certa_responde_204(client: AsyncClient, ana: User) -> None:
    resposta = await client.request(
        "DELETE", URL, json={"password": SENHA}, headers=bearer(ana)
    )

    assert resposta.status_code == 204
    assert resposta.content == b""


async def test_com_a_senha_errada_responde_422(client: AsyncClient, ana: User) -> None:
    resposta = await client.request(
        "DELETE", URL, json={"password": "errada"}, headers=bearer(ana)
    )

    assert resposta.status_code == 422
    assert resposta.json() == {"error": "invalid_current_password"}


async def test_sem_token_responde_401(client: AsyncClient) -> None:
    resposta = await client.request("DELETE", URL, json={"password": SENHA})

    assert resposta.status_code == 401
    assert resposta.json() == {"error": "not_authenticated"}


async def test_campo_a_mais_responde_422_invalid_request(
    client: AsyncClient, ana: User
) -> None:
    resposta = await client.request(
        "DELETE", URL, json={"password": SENHA, "x": 1}, headers=bearer(ana)
    )

    assert resposta.status_code == 422
    assert resposta.json()["error"] == "invalid_request"


async def test_depois_de_apagar_o_mesmo_token_responde_401(
    client: AsyncClient, ana: User
) -> None:
    await client.request("DELETE", URL, json={"password": SENHA}, headers=bearer(ana))

    de_novo = await client.request(
        "DELETE", URL, json={"password": SENHA}, headers=bearer(ana)
    )

    assert de_novo.status_code == 401
    assert de_novo.json() == {"error": "invalid_token"}
