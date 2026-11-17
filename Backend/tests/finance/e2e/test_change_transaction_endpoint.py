import uuid
from collections.abc import AsyncIterator
from dataclasses import dataclass
from datetime import date

import pytest
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient

from app.finance.application.use_cases.delete_transaction import (
    DeleteTransactionInputPort,
    DeleteTransactionInteractor,
    DeleteTransactionOutputPort,
)
from app.finance.application.use_cases.update_transaction import (
    UpdateTransactionInputPort,
    UpdateTransactionInteractor,
    UpdateTransactionOutputPort,
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
from tests.finance.fakes.fake_categorizer import FakeCategorizer
from tests.finance.fakes.fake_unit_of_work import FakeUnitOfWork
from tests.users.fakes.fake_token_verifier import FakeTokenVerifier

ANA, BIA = uuid.uuid4(), uuid.uuid4()
CARTEIRA = Account.open(OwnerId(ANA), AccountName("Carteira"), AccountKind.WALLET)


def token(pessoa: uuid.UUID) -> dict[str, str]:
    return {"Authorization": f"Bearer token-falso:{pessoa}"}


@dataclass
class Api:
    client: AsyncClient
    uow: FakeUnitOfWork
    padaria: Transaction


@pytest.fixture
async def api() -> AsyncIterator[Api]:
    uow = FakeUnitOfWork()
    await uow.accounts.add(CARTEIRA)
    padaria = Transaction.record(
        owner=OwnerId(ANA),
        account=CARTEIRA.id,
        kind=TransactionKind.EXPENSE,
        amount=Money(4590),
        description=Description("Padaria"),
        category=Category("mercado"),
        occurred_on=date(2026, 11, 7),
    )
    await uow.transactions.add(padaria)

    def corrigir(presenter: UpdateTransactionOutputPort) -> UpdateTransactionInputPort:
        return UpdateTransactionInteractor(
            uow=uow,
            categorizer=FakeCategorizer(Category("mercado")),
            presenter=presenter,
        )

    def apagar(presenter: DeleteTransactionOutputPort) -> DeleteTransactionInputPort:
        return DeleteTransactionInteractor(uow=uow, presenter=presenter)

    app = FastAPI()
    install_error_handlers(app)
    app.include_router(router)
    app.state.update_transaction = corrigir
    app.state.delete_transaction = apagar
    app.state.token_verifier = FakeTokenVerifier()

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://teste") as client:
        yield Api(client, uow, padaria)


def url(api: Api) -> str:
    return f"/api/v1/transactions/{api.padaria.id.value}"


CORRECAO = {
    "account_id": str(CARTEIRA.id.value),
    "kind": "expense",
    "amount_cents": 4950,
    "description": "Padaria São Jorge",
    "occurred_on": "2026-11-08",
}


async def test_corrigir_responde_200_com_a_transacao_como_ficou(api: Api) -> None:
    resposta = await api.client.put(url(api), json=CORRECAO, headers=token(ANA))

    assert resposta.status_code == 200
    assert resposta.json()["id"] == str(api.padaria.id.value)
    assert resposta.json()["amount_cents"] == 4950
    [gravada] = api.uow.transactions.stored
    assert gravada.amount == Money(4950)


async def test_corrigir_a_de_outra_pessoa_responde_404(api: Api) -> None:
    resposta = await api.client.put(url(api), json=CORRECAO, headers=token(BIA))

    assert resposta.status_code == 404
    assert resposta.json() == {"error": "transaction_not_found"}


async def test_corrigir_com_dado_recusado_responde_422(api: Api) -> None:
    resposta = await api.client.put(
        url(api), json={**CORRECAO, "amount_cents": 0}, headers=token(ANA)
    )

    assert resposta.status_code == 422
    assert resposta.json()["error"] == "invalid_transaction"


async def test_id_fora_do_formato_e_recusado_pelo_formato(api: Api) -> None:
    resposta = await api.client.delete(
        "/api/v1/transactions/padaria", headers=token(ANA)
    )

    assert resposta.status_code == 422
    assert resposta.json() == {
        "error": "invalid_request",
        "fields": [{"field": "transaction_id", "problem": "uuid_parsing"}],
    }


async def test_apagar_responde_204_e_a_transacao_some(api: Api) -> None:
    resposta = await api.client.delete(url(api), headers=token(ANA))

    assert resposta.status_code == 204
    assert resposta.content == b""
    assert api.uow.transactions.stored == []


async def test_apagar_a_de_outra_pessoa_responde_404_e_nao_apaga(api: Api) -> None:
    resposta = await api.client.delete(url(api), headers=token(BIA))

    assert resposta.status_code == 404
    assert api.uow.transactions.stored == [api.padaria]


async def test_sem_token_responde_401(api: Api) -> None:
    assert (await api.client.put(url(api), json=CORRECAO)).status_code == 401
    assert (await api.client.delete(url(api))).status_code == 401


def test_a_documentacao_mostra_as_rotas_novas() -> None:
    app = FastAPI()
    app.include_router(router)

    caminho = app.openapi()["paths"]["/api/v1/transactions/{transaction_id}"]

    assert {"401", "404", "422"} <= set(caminho["put"]["responses"])
    assert {"204", "401", "404"} <= set(caminho["delete"]["responses"])
