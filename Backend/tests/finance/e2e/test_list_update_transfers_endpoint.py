import uuid
from collections.abc import AsyncIterator

import pytest
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient

from app.finance.application.use_cases.create_transfer import (
    CreateTransferInputPort,
    CreateTransferInteractor,
    CreateTransferOutputPort,
)
from app.finance.application.use_cases.list_transfers import (
    ListTransfersInputPort,
    ListTransfersInteractor,
    ListTransfersOutputPort,
)
from app.finance.application.use_cases.update_transfer import (
    UpdateTransferInputPort,
    UpdateTransferInteractor,
    UpdateTransferOutputPort,
)
from app.finance.domain.entities.account import Account
from app.finance.domain.value_objects.account_kind import AccountKind
from app.finance.domain.value_objects.account_name import AccountName
from app.finance.domain.value_objects.owner_id import OwnerId
from app.finance.presentation.api.v1.routers.transfers import router
from app.shared.presentation.api.error_handlers import install_error_handlers
from tests.finance.fakes.fake_unit_of_work import FakeUnitOfWork
from tests.users.fakes.fake_access_token_check import FakeAccessTokenCheck
from tests.users.fakes.fake_token_verifier import FakeTokenVerifier

URL = "/api/v1/transfers"
ANA, BIA = uuid.uuid4(), uuid.uuid4()
CORRENTE = Account.open(OwnerId(ANA), AccountName("Corrente"), AccountKind.CHECKING)
CARTAO = Account.open(OwnerId(ANA), AccountName("Cartão"), AccountKind.CREDIT_CARD)
CORRENTE_BIA = Account.open(OwnerId(BIA), AccountName("Corrente"), AccountKind.CHECKING)
CARTEIRA_BIA = Account.open(OwnerId(BIA), AccountName("Carteira"), AccountKind.WALLET)
CORPO_BIA = {
    "from_account_id": str(CORRENTE_BIA.id.value),
    "to_account_id": str(CARTEIRA_BIA.id.value),
    "amount_cents": 3000,
    "description": "Saque",
    "occurred_on": "2026-11-12",
}
CORPO = {
    "from_account_id": str(CORRENTE.id.value),
    "to_account_id": str(CARTAO.id.value),
    "amount_cents": 150000,
    "description": "Fatura",
    "occurred_on": "2026-11-10",
}
PERIODO = {"from": "2026-11-01", "to": "2026-11-30"}


def token(pessoa: uuid.UUID) -> dict[str, str]:
    return {"Authorization": f"Bearer token-falso:{pessoa}"}


@pytest.fixture
async def client() -> AsyncIterator[AsyncClient]:
    uow = FakeUnitOfWork()
    for conta in (CORRENTE, CARTAO, CORRENTE_BIA, CARTEIRA_BIA):
        await uow.accounts.add(conta)

    def criar(presenter: CreateTransferOutputPort) -> CreateTransferInputPort:
        return CreateTransferInteractor(uow=uow, presenter=presenter)

    def listar(presenter: ListTransfersOutputPort) -> ListTransfersInputPort:
        return ListTransfersInteractor(uow=uow, presenter=presenter)

    def corrigir(presenter: UpdateTransferOutputPort) -> UpdateTransferInputPort:
        return UpdateTransferInteractor(uow=uow, presenter=presenter)

    app = FastAPI()
    install_error_handlers(app)
    app.include_router(router)
    app.state.create_transfer = criar
    app.state.list_transfers = listar
    app.state.update_transfer = corrigir
    app.state.token_verifier = FakeTokenVerifier()
    app.state.access_token_check = FakeAccessTokenCheck()

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://teste") as client:
        yield client


async def criar_uma(client: AsyncClient) -> str:
    resposta = await client.post(URL, json=CORPO, headers=token(ANA))
    return str(resposta.json()["id"])


async def test_listar_responde_200_com_from_to_e_no_store(client: AsyncClient) -> None:
    transfer_id = await criar_uma(client)

    resposta = await client.get(URL, params=PERIODO, headers=token(ANA))

    assert resposta.status_code == 200
    assert resposta.headers["cache-control"] == "no-store"
    assert resposta.json() == {
        "from": "2026-11-01",
        "to": "2026-11-30",
        "transfers": [{"id": transfer_id, **CORPO}],
    }


async def test_cada_pessoa_lista_so_as_proprias(client: AsyncClient) -> None:
    await criar_uma(client)

    resposta = await client.get(URL, params=PERIODO, headers=token(BIA))

    assert resposta.json()["transfers"] == []


async def test_periodo_longo_demais_responde_422_invalid_period(
    client: AsyncClient,
) -> None:
    resposta = await client.get(
        URL, params={"from": "2026-01-01", "to": "2028-01-01"}, headers=token(ANA)
    )

    assert resposta.status_code == 422
    assert resposta.json() == {
        "error": "invalid_period",
        "fields": [{"field": "to", "problem": "too_long"}],
    }


async def test_sem_parametros_ou_data_mal_formada_responde_invalid_request(
    client: AsyncClient,
) -> None:
    sem = await client.get(URL, headers=token(ANA))
    ruim = await client.get(
        URL, params={"from": "ontem", "to": "hoje"}, headers=token(ANA)
    )

    assert sem.status_code == ruim.status_code == 422
    assert sem.json()["error"] == ruim.json()["error"] == "invalid_request"


async def test_corrigir_responde_200_e_no_store(client: AsyncClient) -> None:
    transfer_id = await criar_uma(client)

    resposta = await client.put(
        f"{URL}/{transfer_id}",
        json={**CORPO, "amount_cents": 160000},
        headers=token(ANA),
    )

    assert resposta.status_code == 200
    assert resposta.headers["cache-control"] == "no-store"
    assert resposta.json() == {"id": transfer_id, **CORPO, "amount_cents": 160000}


async def test_corrigir_com_a_mesma_conta_responde_422(client: AsyncClient) -> None:
    transfer_id = await criar_uma(client)

    resposta = await client.put(
        f"{URL}/{transfer_id}",
        json={**CORPO, "to_account_id": CORPO["from_account_id"]},
        headers=token(ANA),
    )

    assert resposta.status_code == 422
    assert resposta.json()["error"] == "invalid_transfer"


async def test_corrigir_a_de_outra_pessoa_responde_404(client: AsyncClient) -> None:
    transfer_id = await criar_uma(client)

    resposta = await client.put(f"{URL}/{transfer_id}", json=CORPO, headers=token(BIA))

    assert resposta.status_code == 404
    assert resposta.json() == {"error": "transfer_not_found"}


async def test_corpo_com_campo_a_mais_ou_id_ruim_responde_invalid_request(
    client: AsyncClient,
) -> None:
    transfer_id = await criar_uma(client)

    extra = await client.put(
        f"{URL}/{transfer_id}", json={**CORPO, "x": 1}, headers=token(ANA)
    )
    ruim = await client.put(f"{URL}/nao-e-uuid", json=CORPO, headers=token(ANA))

    assert extra.status_code == ruim.status_code == 422
    assert extra.json()["error"] == ruim.json()["error"] == "invalid_request"


async def test_sem_token_responde_401(client: AsyncClient) -> None:
    listar = await client.get(URL, params=PERIODO)
    corrigir = await client.put(f"{URL}/{uuid.uuid4()}", json=CORPO)

    assert listar.status_code == corrigir.status_code == 401


@pytest.mark.parametrize(
    ("campo_alheio", "conta_alheia"),
    [("from_account_id", CORRENTE), ("to_account_id", CARTAO)],
)
async def test_corrigir_a_propria_apontando_conta_de_outra_pessoa_responde_422(
    client: AsyncClient, campo_alheio: str, conta_alheia: Account
) -> None:
    criada = await client.post(URL, json=CORPO_BIA, headers=token(BIA))
    transfer_id = criada.json()["id"]

    resposta = await client.put(
        f"{URL}/{transfer_id}",
        json={**CORPO_BIA, campo_alheio: str(conta_alheia.id.value)},
        headers=token(BIA),
    )

    assert resposta.status_code == 422
    assert resposta.json() == {
        "error": "invalid_transfer",
        "fields": [{"field": campo_alheio, "problem": "not_found"}],
    }
    lista = await client.get(URL, params=PERIODO, headers=token(BIA))
    assert lista.json()["transfers"] == [{"id": transfer_id, **CORPO_BIA}]
    assert (await client.get(URL, params=PERIODO, headers=token(ANA))).json()[
        "transfers"
    ] == []


async def test_corrigir_a_de_outra_pessoa_com_contas_proprias_responde_404(
    client: AsyncClient,
) -> None:
    transfer_id = await criar_uma(client)

    resposta = await client.put(
        f"{URL}/{transfer_id}", json=CORPO_BIA, headers=token(BIA)
    )

    assert resposta.status_code == 404
    assert resposta.json() == {"error": "transfer_not_found"}
    lista = await client.get(URL, params=PERIODO, headers=token(ANA))
    assert lista.json()["transfers"] == [{"id": transfer_id, **CORPO}]
