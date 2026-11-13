import uuid
from collections.abc import AsyncIterator

import pytest
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient

from app.finance.application.use_cases.list_categories import (
    ListCategoriesInputPort,
    ListCategoriesInteractor,
    ListCategoriesOutputPort,
)
from app.finance.presentation.api.v1.routers.categories import router
from app.shared.presentation.api.error_handlers import install_error_handlers
from tests.finance.fakes.fake_unit_of_work import FakeUnitOfWork
from tests.users.fakes.fake_token_verifier import FakeTokenVerifier

URL = "/api/v1/categories"
TOKEN = {"Authorization": f"Bearer token-falso:{uuid.uuid4()}"}


@pytest.fixture
async def client() -> AsyncIterator[AsyncClient]:
    uow = FakeUnitOfWork()

    def listar(presenter: ListCategoriesOutputPort) -> ListCategoriesInputPort:
        return ListCategoriesInteractor(uow=uow, presenter=presenter)

    app = FastAPI()
    install_error_handlers(app)
    app.include_router(router)
    app.state.list_categories = listar
    app.state.token_verifier = FakeTokenVerifier()

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://teste") as client:
        yield client


async def test_lista_as_categorias(client: AsyncClient) -> None:
    resposta = await client.get(URL, headers=TOKEN)

    assert resposta.status_code == 200
    categorias = resposta.json()["categories"]
    assert {"kind": "expense", "name": "saude", "label": "Saúde"} in categorias
    assert len(categorias) == 9


async def test_sem_token_responde_401(client: AsyncClient) -> None:
    resposta = await client.get(URL)

    assert resposta.status_code == 401
    assert resposta.json() == {"error": "not_authenticated"}


def test_a_documentacao_mostra_que_a_rota_exige_token() -> None:
    app = FastAPI()
    app.include_router(router)

    operacao = app.openapi()["paths"][URL]["get"]

    assert operacao["security"] == [{"HTTPBearer": []}]
    assert {"200", "401"} <= set(operacao["responses"])
