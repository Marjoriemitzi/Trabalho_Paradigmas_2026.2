import uuid
from collections.abc import AsyncIterator
from dataclasses import dataclass

import pytest
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient

from app.finance.application.use_cases.create_transfer import (
    CreateTransferInputPort,
    CreateTransferInteractor,
    CreateTransferOutputPort,
)
from app.finance.application.use_cases.delete_transfer import (
    DeleteTransferInputPort,
    DeleteTransferInteractor,
    DeleteTransferOutputPort,
)
from app.finance.domain.entities.account import Account
from app.finance.domain.value_objects.account_kind import AccountKind
from app.finance.domain.value_objects.account_name import AccountName
from app.finance.domain.value_objects.owner_id import OwnerId
from app.finance.presentation.api.v1.routers.transfers import router
from app.shared.presentation.api.error_handlers import install_error_handlers
from tests.finance.fakes.fake_unit_of_work import FakeUnitOfWork
from tests.users.fakes.fake_token_verifier import FakeTokenVerifier

URL = "/api/v1/transfers"
ANA, BIA = uuid.uuid4(), uuid.uuid4()
CORRENTE = Account.open(OwnerId(ANA), AccountName("Corrente"), AccountKind.CHECKING)
CARTAO = Account.open(OwnerId(ANA), AccountName("Cartão"), AccountKind.CREDIT_CARD)
FATURA = {
    "from_account_id": str(CORRENTE.id.value),
    "to_account_id": str(CARTAO.id.value),
    "amount_cents": 150000,
    "description": "Pagamento da fatura",
    "occurred_on": "2026-11-10",
}


def token(pessoa: uuid.UUID) -> dict[str, str]:
    return {"Authorization": f"Bearer token-falso:{pessoa}"}


@dataclass
class Api:
    client: AsyncClient
    uow: FakeUnitOfWork


@pytest.fixture
async def api() -> AsyncIterator[Api]:
    uow = FakeUnitOfWork()
    for conta in (CORRENTE, CARTAO):
        await uow.accounts.add(conta)

    def criar(presenter: CreateTransferOutputPort) -> CreateTransferInputPort:
        return CreateTransferInteractor(uow=uow, presenter=presenter)

    def apagar(presenter: DeleteTransferOutputPort) -> DeleteTransferInputPort:
        return DeleteTransferInteractor(uow=uow, presenter=presenter)

    app = FastAPI()
    install_error_handlers(app)
    app.include_router(router)
    app.state.create_transfer = criar
    app.state.delete_transfer = apagar
    app.state.token_verifier = FakeTokenVerifier()

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://teste") as client:
        yield Api(client, uow)


async def test_criar_e_apagar_uma_transferencia(api: Api) -> None:
    criada = await api.client.post(URL, json=FATURA, headers=token(ANA))

    assert criada.status_code == 201
    assert criada.json()["amount_cents"] == 150000
    apagada = await api.client.delete(
        f"{URL}/{criada.json()['id']}", headers=token(ANA)
    )
    assert apagada.status_code == 204
    assert api.uow.transfers.stored == []


async def test_mesma_conta_nos_dois_lados_e_recusada(api: Api) -> None:
    resposta = await api.client.post(
        URL,
        json={**FATURA, "to_account_id": FATURA["from_account_id"]},
        headers=token(ANA),
    )

    assert resposta.status_code == 422
    assert resposta.json() == {
        "error": "invalid_transfer",
        "fields": [{"field": "to_account_id", "problem": "same_account"}],
    }


async def test_contas_de_outra_pessoa_sao_recusadas(api: Api) -> None:
    resposta = await api.client.post(URL, json=FATURA, headers=token(BIA))

    assert resposta.status_code == 422
    assert resposta.json()["fields"] == [
        {"field": "from_account_id", "problem": "not_found"}
    ]


async def test_apagar_a_que_nao_existe_responde_404(api: Api) -> None:
    resposta = await api.client.delete(f"{URL}/{uuid.uuid4()}", headers=token(ANA))

    assert resposta.status_code == 404
    assert resposta.json() == {"error": "transfer_not_found"}


async def test_valor_em_texto_e_recusado_pelo_formato(api: Api) -> None:
    resposta = await api.client.post(
        URL, json={**FATURA, "amount_cents": "1500"}, headers=token(ANA)
    )

    assert resposta.status_code == 422
    assert resposta.json()["error"] == "invalid_request"


async def test_sem_token_responde_401(api: Api) -> None:
    assert (await api.client.post(URL, json=FATURA)).status_code == 401
    assert (await api.client.delete(f"{URL}/{uuid.uuid4()}")).status_code == 401


def test_a_documentacao_mostra_as_rotas() -> None:
    app = FastAPI()
    app.include_router(router)

    caminhos = app.openapi()["paths"]

    assert {"201", "401", "422"} <= set(caminhos[URL]["post"]["responses"])
    assert {"204", "401", "404"} <= set(
        caminhos[f"{URL}/{{transfer_id}}"]["delete"]["responses"]
    )
