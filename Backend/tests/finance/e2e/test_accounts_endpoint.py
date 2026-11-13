import uuid
from collections.abc import AsyncIterator

import pytest
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient

from app.finance.application.use_cases.create_account import (
    CreateAccountInputPort,
    CreateAccountInteractor,
    CreateAccountOutputPort,
)
from app.finance.application.use_cases.list_accounts import (
    ListAccountsInputPort,
    ListAccountsInteractor,
    ListAccountsOutputPort,
)
from app.finance.presentation.api.v1.routers.accounts import router
from app.shared.presentation.api.error_handlers import install_error_handlers
from tests.finance.fakes.fake_unit_of_work import FakeUnitOfWork
from tests.users.fakes.fake_token_verifier import FakeTokenVerifier

URL = "/api/v1/accounts"
ANA, BIA = uuid.uuid4(), uuid.uuid4()


def token(pessoa: uuid.UUID) -> dict[str, str]:
    return {"Authorization": f"Bearer token-falso:{pessoa}"}


@pytest.fixture
async def client() -> AsyncIterator[AsyncClient]:
    uow = FakeUnitOfWork()

    def criar(presenter: CreateAccountOutputPort) -> CreateAccountInputPort:
        return CreateAccountInteractor(uow=uow, presenter=presenter)

    def listar(presenter: ListAccountsOutputPort) -> ListAccountsInputPort:
        return ListAccountsInteractor(uow=uow, presenter=presenter)

    app = FastAPI()
    install_error_handlers(app)
    app.include_router(router)
    app.state.create_account = criar
    app.state.list_accounts = listar
    app.state.token_verifier = FakeTokenVerifier()

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://teste") as client:
        yield client


async def test_abrir_e_listar_contas(client: AsyncClient) -> None:
    criada = await client.post(
        URL, json={"name": "Nubank", "kind": "checking"}, headers=token(ANA)
    )

    assert criada.status_code == 201
    lista = await client.get(URL, headers=token(ANA))
    assert lista.status_code == 200
    assert lista.json() == {"accounts": [{**criada.json(), "balance_cents": 0}]}


async def test_cada_pessoa_so_ve_as_proprias_contas(client: AsyncClient) -> None:
    await client.post(
        URL, json={"name": "Nubank", "kind": "checking"}, headers=token(ANA)
    )

    lista = await client.get(URL, headers=token(BIA))

    assert lista.json() == {"accounts": []}


async def test_nome_repetido_responde_409(client: AsyncClient) -> None:
    await client.post(
        URL, json={"name": "Nubank", "kind": "checking"}, headers=token(ANA)
    )

    resposta = await client.post(
        URL, json={"name": "nubank", "kind": "credit_card"}, headers=token(ANA)
    )

    assert resposta.status_code == 409
    assert resposta.json() == {"error": "account_name_taken"}


async def test_sem_token_responde_401(client: AsyncClient) -> None:
    assert (await client.get(URL)).status_code == 401
    assert (
        await client.post(URL, json={"name": "X", "kind": "wallet"})
    ).status_code == 401
