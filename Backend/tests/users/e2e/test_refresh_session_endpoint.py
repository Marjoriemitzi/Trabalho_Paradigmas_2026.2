from collections.abc import AsyncIterator

import pytest
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient

from app.shared.presentation.api.error_handlers import install_error_handlers
from app.users.application.session import hash_refresh_token
from app.users.application.use_cases.logout import (
    LogoutInputPort,
    LogoutInteractor,
    LogoutOutputPort,
)
from app.users.application.use_cases.refresh_session import (
    RefreshSessionInputPort,
    RefreshSessionInteractor,
    RefreshSessionOutputPort,
)
from app.users.domain.entities.user import User
from app.users.domain.value_objects.email import Email
from app.users.domain.value_objects.password import PasswordHash
from app.users.presentation.api.v1.routers.auth import router
from tests.users.fakes.fake_clock import FakeClock
from tests.users.fakes.fake_session_issuer import fake_session_issuer
from tests.users.fakes.fake_token_verifier import FakeTokenVerifier
from tests.users.fakes.fake_unit_of_work import FakeUnitOfWork

REFRESH = "/api/v1/auth/refresh"
LOGOUT = "/api/v1/auth/logout"


@pytest.fixture
async def client() -> AsyncIterator[tuple[AsyncClient, str, FakeUnitOfWork]]:
    uow = FakeUnitOfWork()
    clock = FakeClock()
    issuer = fake_session_issuer(clock)
    ana = User.register(Email("ana@acme.com"), PasswordHash("hash"))
    await uow.users.add(ana)
    sessao = await issuer.issue(uow, ana)

    def renovar(presenter: RefreshSessionOutputPort) -> RefreshSessionInputPort:
        return RefreshSessionInteractor(
            uow=uow, issuer=issuer, clock=clock, presenter=presenter
        )

    def sair(presenter: LogoutOutputPort) -> LogoutInputPort:
        return LogoutInteractor(uow=uow, clock=clock, presenter=presenter)

    app = FastAPI()
    install_error_handlers(app)
    app.include_router(router)
    app.state.refresh_session = renovar
    app.state.logout = sair
    app.state.token_verifier = FakeTokenVerifier()

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://teste") as http:
        yield http, sessao.refresh_token, uow


async def test_renovar_responde_200_com_o_par_novo(
    client: tuple[AsyncClient, str, FakeUnitOfWork],
) -> None:
    http, refresh, _ = client

    resposta = await http.post(REFRESH, json={"refresh_token": refresh})

    assert resposta.status_code == 200
    assert resposta.headers["cache-control"] == "no-store"
    assert resposta.json()["refresh_token"] != refresh
    assert resposta.json()["token_type"] == "bearer"


async def test_refresh_token_usado_de_novo_responde_401(
    client: tuple[AsyncClient, str, FakeUnitOfWork],
) -> None:
    http, refresh, _ = client
    await http.post(REFRESH, json={"refresh_token": refresh})

    resposta = await http.post(REFRESH, json={"refresh_token": refresh})

    assert resposta.status_code == 401
    assert resposta.json() == {"error": "invalid_refresh_token"}


async def test_pedido_sem_o_campo_ou_com_campo_a_mais_responde_422(
    client: tuple[AsyncClient, str, FakeUnitOfWork],
) -> None:
    http, refresh, _ = client

    sem = await http.post(REFRESH, json={})
    extra = await http.post(REFRESH, json={"refresh_token": refresh, "x": 1})
    vazio = await http.post(LOGOUT, json={"refresh_token": ""})

    for resposta in (sem, extra, vazio):
        assert resposta.status_code == 422
        assert resposta.json()["error"] == "invalid_request"


async def test_logout_responde_204_e_vale_so_uma_vez_para_renovar(
    client: tuple[AsyncClient, str, FakeUnitOfWork],
) -> None:
    http, refresh, _ = client

    saida = await http.post(LOGOUT, json={"refresh_token": refresh})
    repetida = await http.post(LOGOUT, json={"refresh_token": refresh})
    renovar = await http.post(REFRESH, json={"refresh_token": refresh})

    assert saida.status_code == repetida.status_code == 204
    assert renovar.status_code == 401


async def test_logout_com_token_desconhecido_tambem_responde_204(
    client: tuple[AsyncClient, str, FakeUnitOfWork],
) -> None:
    http, _, _ = client

    resposta = await http.post(LOGOUT, json={"refresh_token": "nunca-existiu"})

    assert resposta.status_code == 204


async def test_logout_com_bearer_valido_responde_204_e_bloqueia_o_access_token(
    client: tuple[AsyncClient, str, FakeUnitOfWork],
) -> None:
    http, refresh, uow = client
    gravado = await uow.refresh_tokens.get_by_hash(hash_refresh_token(refresh))
    assert gravado is not None
    dono = gravado.user_id.value

    resposta = await http.post(
        LOGOUT,
        json={"refresh_token": refresh},
        headers={"Authorization": f"Bearer token-falso:{dono}"},
    )

    assert resposta.status_code == 204
    assert await uow.token_blocklist.contains(dono) is True


async def test_logout_com_bearer_invalido_e_ignorado_e_nao_da_401(
    client: tuple[AsyncClient, str, FakeUnitOfWork],
) -> None:
    http, refresh, _ = client

    resposta = await http.post(
        LOGOUT,
        json={"refresh_token": refresh},
        headers={"Authorization": "Bearer lixo"},
    )

    assert resposta.status_code == 204
