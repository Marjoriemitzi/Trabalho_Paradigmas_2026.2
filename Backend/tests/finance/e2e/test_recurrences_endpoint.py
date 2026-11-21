import uuid
from collections.abc import AsyncIterator
from datetime import date

import pytest
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient

from app.finance.application.use_cases.create_recurrence import (
    CreateRecurrenceInputPort,
    CreateRecurrenceInteractor,
    CreateRecurrenceOutputPort,
)
from app.finance.application.use_cases.delete_recurrence import (
    DeleteRecurrenceInputPort,
    DeleteRecurrenceInteractor,
    DeleteRecurrenceOutputPort,
)
from app.finance.application.use_cases.list_recurrences import (
    ListRecurrencesInputPort,
    ListRecurrencesInteractor,
    ListRecurrencesOutputPort,
)
from app.finance.application.use_cases.update_recurrence import (
    UpdateRecurrenceInputPort,
    UpdateRecurrenceInteractor,
    UpdateRecurrenceOutputPort,
)
from app.finance.domain.entities.account import Account
from app.finance.domain.value_objects.account_kind import AccountKind
from app.finance.domain.value_objects.account_name import AccountName
from app.finance.domain.value_objects.owner_id import OwnerId
from app.finance.presentation.api.v1.routers.recurrences import router
from app.shared.presentation.api.error_handlers import install_error_handlers
from tests.finance.fakes.fake_recurrence_rules import FakeRecurrenceRules
from tests.finance.fakes.fake_unit_of_work import FakeUnitOfWork
from tests.shared.fakes.fixed_clock import FixedClock
from tests.users.fakes.fake_access_token_check import FakeAccessTokenCheck
from tests.users.fakes.fake_token_verifier import FakeTokenVerifier

URL = "/api/v1/recurrences"
ANA, BIA = uuid.uuid4(), uuid.uuid4()
CORRENTE = Account.open(OwnerId(ANA), AccountName("Corrente"), AccountKind.CHECKING)
CORPO = {
    "account_id": str(CORRENTE.id.value),
    "kind": "expense",
    "amount_cents": 150000,
    "description": "Aluguel",
    "category": "moradia",
    "frequency": "monthly",
    "day": 5,
    "starts_on": "2026-12-01",
    "ends_on": None,
}


def token(pessoa: uuid.UUID) -> dict[str, str]:
    return {"Authorization": f"Bearer token-falso:{pessoa}"}


@pytest.fixture
async def client() -> AsyncIterator[AsyncClient]:
    uow = FakeUnitOfWork()
    await uow.accounts.add(CORRENTE)
    rules, clock = FakeRecurrenceRules(), FixedClock(date(2026, 11, 20))

    def criar(presenter: CreateRecurrenceOutputPort) -> CreateRecurrenceInputPort:
        return CreateRecurrenceInteractor(
            uow=uow, rules=rules, clock=clock, presenter=presenter
        )

    def corrigir(presenter: UpdateRecurrenceOutputPort) -> UpdateRecurrenceInputPort:
        return UpdateRecurrenceInteractor(
            uow=uow, rules=rules, clock=clock, presenter=presenter
        )

    def apagar(presenter: DeleteRecurrenceOutputPort) -> DeleteRecurrenceInputPort:
        return DeleteRecurrenceInteractor(uow=uow, presenter=presenter)

    def listar(presenter: ListRecurrencesOutputPort) -> ListRecurrencesInputPort:
        return ListRecurrencesInteractor(
            uow=uow, rules=rules, clock=clock, presenter=presenter
        )

    app = FastAPI()
    install_error_handlers(app)
    app.include_router(router)
    app.state.create_recurrence = criar
    app.state.update_recurrence = corrigir
    app.state.delete_recurrence = apagar
    app.state.list_recurrences = listar
    app.state.token_verifier = FakeTokenVerifier()
    app.state.access_token_check = FakeAccessTokenCheck()

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://teste"
    ) as http:
        yield http


async def criar_uma(http: AsyncClient) -> str:
    resposta = await http.post(URL, json=CORPO, headers=token(ANA))
    return str(resposta.json()["id"])


async def test_criar_responde_201_com_a_proxima_data(client: AsyncClient) -> None:
    resposta = await client.post(URL, json=CORPO, headers=token(ANA))

    assert resposta.status_code == 201
    assert resposta.headers["cache-control"] == "no-store"
    assert resposta.json()["next_occurrence_on"] == "2026-12-05"
    assert resposta.json()["category"] == "moradia"


async def test_criar_sem_categoria_responde_com_null(client: AsyncClient) -> None:
    sem_categoria = {k: v for k, v in CORPO.items() if k != "category"}

    resposta = await client.post(URL, json=sem_categoria, headers=token(ANA))

    assert resposta.status_code == 201
    assert resposta.json()["category"] is None


async def test_dado_recusado_responde_422_invalid_recurrence(
    client: AsyncClient,
) -> None:
    resposta = await client.post(URL, json={**CORPO, "day": 32}, headers=token(ANA))

    assert resposta.status_code == 422
    assert resposta.json() == {
        "error": "invalid_recurrence",
        "fields": [{"field": "day", "problem": "out_of_range"}],
    }


async def test_campo_a_mais_ou_valor_nao_inteiro_responde_invalid_request(
    client: AsyncClient,
) -> None:
    extra = await client.post(URL, json={**CORPO, "x": 1}, headers=token(ANA))
    quebrado = await client.post(
        URL, json={**CORPO, "amount_cents": 10.5}, headers=token(ANA)
    )

    assert extra.status_code == quebrado.status_code == 422
    assert extra.json()["error"] == quebrado.json()["error"] == "invalid_request"


async def test_listar_traz_so_as_da_pessoa_com_no_store(client: AsyncClient) -> None:
    await criar_uma(client)

    minha = await client.get(URL, headers=token(ANA))
    da_bia = await client.get(URL, headers=token(BIA))

    assert minha.status_code == 200
    assert minha.headers["cache-control"] == "no-store"
    assert [r["description"] for r in minha.json()["recurrences"]] == ["Aluguel"]
    assert da_bia.json() == {"recurrences": []}


async def test_corrigir_responde_200(client: AsyncClient) -> None:
    recorrencia = await criar_uma(client)

    resposta = await client.put(
        f"{URL}/{recorrencia}",
        json={**CORPO, "amount_cents": 160000},
        headers=token(ANA),
    )

    assert resposta.status_code == 200
    assert resposta.json()["amount_cents"] == 160000


async def test_corrigir_e_apagar_a_de_outra_pessoa_respondem_404(
    client: AsyncClient,
) -> None:
    recorrencia = await criar_uma(client)

    corrigir = await client.put(f"{URL}/{recorrencia}", json=CORPO, headers=token(BIA))
    apagar = await client.delete(f"{URL}/{recorrencia}", headers=token(BIA))

    assert corrigir.status_code == apagar.status_code == 404
    assert corrigir.json() == apagar.json() == {"error": "recurrence_not_found"}


async def test_apagar_responde_204(client: AsyncClient) -> None:
    recorrencia = await criar_uma(client)

    resposta = await client.delete(f"{URL}/{recorrencia}", headers=token(ANA))

    assert resposta.status_code == 204


async def test_sem_token_responde_401(client: AsyncClient) -> None:
    listar = await client.get(URL)
    criar = await client.post(URL, json=CORPO)

    assert listar.status_code == criar.status_code == 401
    assert listar.json() == {"error": "not_authenticated"}


async def test_id_que_nao_e_uuid_responde_invalid_request(client: AsyncClient) -> None:
    resposta = await client.delete(f"{URL}/nao-e-uuid", headers=token(ANA))

    assert resposta.status_code == 422
    assert resposta.json()["error"] == "invalid_request"
