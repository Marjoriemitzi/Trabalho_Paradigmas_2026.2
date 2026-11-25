from collections.abc import AsyncIterator

import pytest
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient

from app.shared.presentation.api.error_handlers import install_error_handlers
from app.users.application.use_cases.change_password import (
    ChangePasswordInputPort,
    ChangePasswordInteractor,
    ChangePasswordOutputPort,
)
from app.users.domain.entities.user import User
from app.users.domain.value_objects.email import Email
from app.users.domain.value_objects.password import PasswordHash
from app.users.presentation.api.v1.routers.users import router
from tests.users.fakes.fake_access_token_check import FakeAccessTokenCheck
from tests.users.fakes.fake_clock import FakeClock
from tests.users.fakes.fake_password_hasher import FakePasswordHasher
from tests.users.fakes.fake_password_policy import FakePasswordPolicy
from tests.users.fakes.fake_token_issuer import FakeTokenIssuer
from tests.users.fakes.fake_token_verifier import FakeTokenVerifier
from tests.users.fakes.fake_unit_of_work import FakeUnitOfWork

URL = "/api/v1/users/me/password"
HASH_ATUAL = PasswordHash("hash-falso:S3nha!Antiga123")
ANA = User.register(Email("ana@acme.com"), HASH_ATUAL)
CORPO = {"current_password": "S3nha!Antiga123", "new_password": "N0va!SenhaForte"}


def bearer(user: User) -> dict[str, str]:
    return {"Authorization": f"Bearer {FakeTokenIssuer().issue(user).value}"}


@pytest.fixture
async def client() -> AsyncIterator[AsyncClient]:
    ANA.password_hash = HASH_ATUAL
    uow = FakeUnitOfWork()
    await uow.users.add(ANA)

    def build_interactor(
        presenter: ChangePasswordOutputPort,
    ) -> ChangePasswordInputPort:
        return ChangePasswordInteractor(
            uow=uow,
            hasher=FakePasswordHasher(),
            policy=FakePasswordPolicy(rejects={"fraca": ["too_short"]}),
            clock=FakeClock(),
            presenter=presenter,
        )

    app = FastAPI()
    install_error_handlers(app)
    app.include_router(router)
    app.state.change_password = build_interactor
    app.state.token_verifier = FakeTokenVerifier()
    app.state.access_token_check = FakeAccessTokenCheck(uow.users)

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://teste") as client:
        yield client


async def test_troca_responde_204(client: AsyncClient) -> None:
    resposta = await client.post(URL, json=CORPO, headers=bearer(ANA))

    assert resposta.status_code == 204
    assert resposta.content == b""


async def test_senha_atual_errada_responde_422(client: AsyncClient) -> None:
    corpo = {**CORPO, "current_password": "errada"}

    resposta = await client.post(URL, json=corpo, headers=bearer(ANA))

    assert resposta.status_code == 422
    assert resposta.json() == {"error": "invalid_current_password"}


async def test_senha_nova_fraca_responde_422_com_reasons(client: AsyncClient) -> None:
    corpo = {**CORPO, "new_password": "fraca"}

    resposta = await client.post(URL, json=corpo, headers=bearer(ANA))

    assert resposta.status_code == 422
    assert resposta.json() == {"error": "weak_password", "reasons": ["too_short"]}


async def test_sem_token_responde_401(client: AsyncClient) -> None:
    resposta = await client.post(URL, json=CORPO)

    assert resposta.status_code == 401
    assert resposta.json() == {"error": "not_authenticated"}


async def test_campo_a_mais_responde_422_invalid_request(client: AsyncClient) -> None:
    resposta = await client.post(URL, json={**CORPO, "x": 1}, headers=bearer(ANA))

    assert resposta.status_code == 422
    assert resposta.json()["error"] == "invalid_request"


async def test_usuario_que_nao_existe_mais_responde_401(client: AsyncClient) -> None:
    sumiu = User.register(Email("bia@acme.com"), PasswordHash("hash"))

    resposta = await client.post(URL, json=CORPO, headers=bearer(sumiu))

    assert resposta.status_code == 401
    assert resposta.json() == {"error": "invalid_token"}
