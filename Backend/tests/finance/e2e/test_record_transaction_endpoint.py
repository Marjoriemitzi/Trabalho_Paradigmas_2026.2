import uuid
from collections.abc import AsyncIterator
from dataclasses import dataclass

import pytest
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient

from app.finance.application.use_cases.record_transaction import (
    RecordTransactionInputPort,
    RecordTransactionInteractor,
    RecordTransactionOutputPort,
)
from app.finance.domain.entities.account import Account
from app.finance.domain.value_objects.account_kind import AccountKind
from app.finance.domain.value_objects.account_name import AccountName
from app.finance.domain.value_objects.category import Category
from app.finance.domain.value_objects.owner_id import OwnerId
from app.finance.presentation.api.v1.routers.transactions import router
from app.shared.presentation.api.error_handlers import install_error_handlers
from tests.finance.fakes.fake_categorizer import FakeCategorizer
from tests.finance.fakes.fake_unit_of_work import FakeUnitOfWork
from tests.users.fakes.fake_token_verifier import FakeTokenVerifier

URL = "/api/v1/transactions"
ANA = uuid.uuid4()
TOKEN_DA_ANA = {"Authorization": f"Bearer token-falso:{ANA}"}
CARTEIRA_DA_ANA = Account.open(
    OwnerId(ANA), AccountName("Carteira"), AccountKind.WALLET
)
PEDIDO = {
    "account_id": str(CARTEIRA_DA_ANA.id.value),
    "kind": "expense",
    "amount_cents": 1250,
    "description": "Supermercado",
    "occurred_on": "2026-11-07",
}


@dataclass
class Api:
    client: AsyncClient
    uow: FakeUnitOfWork


@pytest.fixture
async def api() -> AsyncIterator[Api]:
    uow = FakeUnitOfWork()
    await uow.accounts.add(CARTEIRA_DA_ANA)

    def build_interactor(
        presenter: RecordTransactionOutputPort,
    ) -> RecordTransactionInputPort:
        return RecordTransactionInteractor(
            uow=uow,
            categorizer=FakeCategorizer(Category("mercado")),
            presenter=presenter,
        )

    app = FastAPI()
    install_error_handlers(app)
    app.include_router(router)
    app.state.record_transaction = build_interactor
    app.state.token_verifier = FakeTokenVerifier()

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://teste") as client:
        yield Api(client, uow)


async def test_lancamento_responde_201_com_a_categoria_escolhida(api: Api) -> None:
    resposta = await api.client.post(URL, json=PEDIDO, headers=TOKEN_DA_ANA)

    assert resposta.status_code == 201
    corpo = resposta.json()
    assert corpo["amount_cents"] == 1250
    assert corpo["category"] == "mercado"
    assert corpo["occurred_on"] == "2026-11-07"
    assert corpo["warnings"] == []


async def test_a_transacao_e_de_quem_esta_logado(api: Api) -> None:
    await api.client.post(URL, json=PEDIDO, headers=TOKEN_DA_ANA)

    [gravada] = api.uow.transactions.stored
    assert gravada.owner.value == ANA
    assert gravada.account == CARTEIRA_DA_ANA.id


async def test_o_pedido_nao_escolhe_o_dono(api: Api) -> None:
    outro = str(uuid.uuid4())

    resposta = await api.client.post(
        URL, json={**PEDIDO, "owner_id": outro}, headers=TOKEN_DA_ANA
    )

    assert resposta.status_code == 422
    assert resposta.json() == {
        "error": "invalid_request",
        "fields": [{"field": "owner_id", "problem": "extra_forbidden"}],
    }
    assert api.uow.transactions.stored == []


async def test_conta_de_outra_pessoa_e_recusada(api: Api) -> None:
    da_bia = Account.open(OwnerId(uuid.uuid4()), AccountName("Bia"), AccountKind.WALLET)
    await api.uow.accounts.add(da_bia)

    resposta = await api.client.post(
        URL, json={**PEDIDO, "account_id": str(da_bia.id.value)}, headers=TOKEN_DA_ANA
    )

    assert resposta.status_code == 422
    assert resposta.json() == {
        "error": "invalid_transaction",
        "fields": [{"field": "account_id", "problem": "not_found"}],
    }
    assert api.uow.transactions.stored == []


async def test_sem_token_responde_401(api: Api) -> None:
    resposta = await api.client.post(URL, json=PEDIDO)

    assert resposta.status_code == 401
    assert resposta.json() == {"error": "not_authenticated"}


async def test_valor_em_texto_e_recusado_pelo_formato(api: Api) -> None:
    resposta = await api.client.post(
        URL, json={**PEDIDO, "amount_cents": "1250"}, headers=TOKEN_DA_ANA
    )

    assert resposta.status_code == 422
    assert resposta.json() == {
        "error": "invalid_request",
        "fields": [{"field": "amount_cents", "problem": "int_type"}],
    }


async def test_valor_zero_e_recusado_pela_regra_do_dominio(api: Api) -> None:
    resposta = await api.client.post(
        URL, json={**PEDIDO, "amount_cents": 0}, headers=TOKEN_DA_ANA
    )

    assert resposta.status_code == 422
    assert resposta.json() == {
        "error": "invalid_transaction",
        "fields": [{"field": "amount_cents", "problem": "not_positive"}],
    }


def test_a_documentacao_mostra_que_a_rota_exige_token() -> None:
    app = FastAPI()
    app.include_router(router)

    operacao = app.openapi()["paths"][URL]["post"]

    assert operacao["security"] == [{"HTTPBearer": []}]
    assert {"201", "401", "422"} <= set(operacao["responses"])
