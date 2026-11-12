import uuid
from collections.abc import AsyncIterator
from datetime import date

import pytest
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient

from app.finance.application.use_cases.get_statement import (
    GetStatementInputPort,
    GetStatementInteractor,
    GetStatementOutputPort,
)
from app.finance.domain.entities.account import Account
from app.finance.domain.entities.transaction import Transaction
from app.finance.domain.value_objects.account_kind import AccountKind
from app.finance.domain.value_objects.account_name import AccountName
from app.finance.domain.value_objects.category import Category
from app.finance.domain.value_objects.description import Description
from app.finance.domain.value_objects.money import Money
from app.finance.domain.value_objects.owner_id import OwnerId
from app.finance.domain.value_objects.transaction_kind import TransactionKind
from app.finance.presentation.api.v1.routers.transactions import router
from app.shared.presentation.api.error_handlers import install_error_handlers
from tests.finance.fakes.fake_unit_of_work import FakeUnitOfWork
from tests.users.fakes.fake_token_verifier import FakeTokenVerifier

URL = "/api/v1/transactions"
NOVEMBRO = {"from": "2026-11-01", "to": "2026-11-30"}
ANA, BIA = uuid.uuid4(), uuid.uuid4()


def conta(dono: uuid.UUID, nome: str) -> Account:
    return Account.open(OwnerId(dono), AccountName(nome), AccountKind.WALLET)


CARTEIRA_DA_ANA, NUBANK_DA_ANA = conta(ANA, "Carteira"), conta(ANA, "Nubank")
CARTEIRA_DA_BIA = conta(BIA, "Carteira")


def token(pessoa: uuid.UUID) -> dict[str, str]:
    return {"Authorization": f"Bearer token-falso:{pessoa}"}


def lancamento(
    na: Account, dia: date, kind: TransactionKind, cents: int
) -> Transaction:
    return Transaction.record(
        owner=na.owner,
        account=na.id,
        kind=kind,
        amount=Money(cents),
        description=Description("Lançamento"),
        category=Category("outros"),
        occurred_on=dia,
    )


@pytest.fixture
async def client() -> AsyncIterator[AsyncClient]:
    uow = FakeUnitOfWork()
    receita, despesa = TransactionKind.INCOME, TransactionKind.EXPENSE
    for nova in (CARTEIRA_DA_ANA, NUBANK_DA_ANA, CARTEIRA_DA_BIA):
        await uow.accounts.add(nova)
    for transacao in (
        lancamento(CARTEIRA_DA_ANA, date(2026, 10, 20), receita, 100000),
        lancamento(CARTEIRA_DA_ANA, date(2026, 11, 5), receita, 520000),
        lancamento(CARTEIRA_DA_ANA, date(2026, 11, 7), despesa, 4590),
        lancamento(NUBANK_DA_ANA, date(2026, 11, 10), despesa, 12000),
        lancamento(CARTEIRA_DA_BIA, date(2026, 11, 8), despesa, 99900),
    ):
        await uow.transactions.add(transacao)

    def build_interactor(presenter: GetStatementOutputPort) -> GetStatementInputPort:
        return GetStatementInteractor(uow=uow, presenter=presenter)

    app = FastAPI()
    install_error_handlers(app)
    app.include_router(router)
    app.state.get_statement = build_interactor
    app.state.token_verifier = FakeTokenVerifier()

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://teste") as client:
        yield client


async def test_extrato_do_mes_junta_todas_as_contas(client: AsyncClient) -> None:
    resposta = await client.get(URL, params=NOVEMBRO, headers=token(ANA))

    assert resposta.status_code == 200
    corpo = resposta.json()
    assert corpo["from"] == "2026-11-01"
    assert corpo["account_id"] is None
    assert corpo["opening_balance_cents"] == 100000
    assert corpo["closing_balance_cents"] == 100000 + 520000 - 4590 - 12000
    assert [t["amount_cents"] for t in corpo["transactions"]] == [
        520000,
        4590,
        12000,
    ]
    assert resposta.headers["cache-control"] == "no-store"


async def test_extrato_de_uma_conta_so(client: AsyncClient) -> None:
    nubank = str(NUBANK_DA_ANA.id.value)

    resposta = await client.get(
        URL, params={**NOVEMBRO, "account_id": nubank}, headers=token(ANA)
    )

    assert resposta.status_code == 200
    corpo = resposta.json()
    assert corpo["account_id"] == nubank
    assert corpo["opening_balance_cents"] == 0
    assert corpo["closing_balance_cents"] == -12000
    assert [t["account_id"] for t in corpo["transactions"]] == [nubank]


async def test_conta_de_outra_pessoa_responde_404(client: AsyncClient) -> None:
    da_bia = str(CARTEIRA_DA_BIA.id.value)

    resposta = await client.get(
        URL, params={**NOVEMBRO, "account_id": da_bia}, headers=token(ANA)
    )

    assert resposta.status_code == 404
    assert resposta.json() == {"error": "account_not_found"}


async def test_conta_fora_do_formato_e_recusada_pelo_formato(
    client: AsyncClient,
) -> None:
    resposta = await client.get(
        URL, params={**NOVEMBRO, "account_id": "nubank"}, headers=token(ANA)
    )

    assert resposta.status_code == 422
    assert resposta.json() == {
        "error": "invalid_request",
        "fields": [{"field": "account_id", "problem": "uuid_parsing"}],
    }


async def test_cada_pessoa_so_ve_o_proprio_extrato(client: AsyncClient) -> None:
    resposta = await client.get(URL, params=NOVEMBRO, headers=token(BIA))

    corpo = resposta.json()
    assert corpo["opening_balance_cents"] == 0
    assert [t["amount_cents"] for t in corpo["transactions"]] == [99900]


async def test_sem_token_responde_401(client: AsyncClient) -> None:
    resposta = await client.get(URL, params=NOVEMBRO)

    assert resposta.status_code == 401
    assert resposta.json() == {"error": "not_authenticated"}


async def test_sem_as_datas_o_pedido_e_recusado_pelo_formato(
    client: AsyncClient,
) -> None:
    resposta = await client.get(URL, params={"from": "2026-11-01"}, headers=token(ANA))

    assert resposta.status_code == 422
    assert resposta.json() == {
        "error": "invalid_request",
        "fields": [{"field": "to", "problem": "missing"}],
    }


async def test_periodo_ao_contrario_e_recusado_pela_regra_do_dominio(
    client: AsyncClient,
) -> None:
    resposta = await client.get(
        URL, params={"from": "2026-11-30", "to": "2026-11-01"}, headers=token(ANA)
    )

    assert resposta.status_code == 422
    assert resposta.json() == {
        "error": "invalid_period",
        "fields": [{"field": "to", "problem": "end_before_start"}],
    }


def test_a_documentacao_mostra_os_parametros_e_o_token() -> None:
    app = FastAPI()
    app.include_router(router)

    operacao = app.openapi()["paths"][URL]["get"]

    assert operacao["security"] == [{"HTTPBearer": []}]
    assert [p["name"] for p in operacao["parameters"]] == ["from", "to", "account_id"]
    assert {"200", "401", "404", "422"} <= set(operacao["responses"])
