from collections.abc import AsyncIterator

import pytest
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient

from app.shared.presentation.api.error_handlers import install_error_handlers
from app.users.application.use_cases.register_user import (
    RegisterUserInputPort,
    RegisterUserInteractor,
    RegisterUserOutputPort,
)
from app.users.presentation.api.v1.routers.users import router
from tests.users.fakes.fake_password_hasher import FakePasswordHasher
from tests.users.fakes.fake_password_policy import FakePasswordPolicy
from tests.users.fakes.fake_unit_of_work import FakeUnitOfWork

URL = "/api/v1/users"
SENHA = "S3nha!Forte123"


@pytest.fixture
async def client() -> AsyncIterator[AsyncClient]:
    uow = FakeUnitOfWork()
    policy = FakePasswordPolicy(rejects={"123": ["too_short", "no_upper"]})

    def build_interactor(presenter: RegisterUserOutputPort) -> RegisterUserInputPort:
        return RegisterUserInteractor(
            uow=uow, hasher=FakePasswordHasher(), policy=policy, presenter=presenter
        )

    app = FastAPI()
    install_error_handlers(app)
    app.include_router(router)

    app.state.register_user = build_interactor

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://teste") as client:
        yield client


async def test_cadastro_bem_sucedido_responde_201(client: AsyncClient) -> None:
    resposta = await client.post(URL, json={"email": "Ana@Acme.com", "password": SENHA})

    assert resposta.status_code == 201
    corpo = resposta.json()
    assert corpo["email"] == "ana@acme.com"
    assert corpo["role"] == "user"
    assert set(corpo) == {"id", "email", "role"}


async def test_mesmo_email_duas_vezes_responde_409(client: AsyncClient) -> None:
    pedido = {"email": "ana@acme.com", "password": SENHA}
    await client.post(URL, json=pedido)

    resposta = await client.post(URL, json=pedido)

    assert resposta.status_code == 409
    assert resposta.json() == {"error": "email_taken"}


async def test_senha_fraca_responde_422_com_os_motivos(client: AsyncClient) -> None:
    resposta = await client.post(URL, json={"email": "ana@acme.com", "password": "123"})

    assert resposta.status_code == 422
    assert resposta.json() == {
        "error": "weak_password",
        "reasons": ["too_short", "no_upper"],
    }


async def test_email_invalido_responde_422(client: AsyncClient) -> None:
    resposta = await client.post(URL, json={"email": "nao-e-email", "password": SENHA})

    assert resposta.status_code == 422
    assert resposta.json() == {"error": "invalid_email"}


async def test_corpo_sem_campo_obrigatorio_responde_422(client: AsyncClient) -> None:
    resposta = await client.post(URL, json={"email": "ana@acme.com"})

    assert resposta.status_code == 422
    assert resposta.json() == {
        "error": "invalid_request",
        "fields": [{"field": "password", "problem": "missing"}],
    }


async def test_campo_a_mais_no_pedido_e_recusado(client: AsyncClient) -> None:
    resposta = await client.post(
        URL, json={"email": "ana@acme.com", "password": SENHA, "role": "admin"}
    )

    assert resposta.status_code == 422
    assert resposta.json() == {
        "error": "invalid_request",
        "fields": [{"field": "role", "problem": "extra_forbidden"}],
    }
    assert SENHA not in resposta.text


def test_a_documentacao_mostra_todos_os_resultados() -> None:
    app = FastAPI()
    app.include_router(router)

    respostas = app.openapi()["paths"][URL]["post"]["responses"]

    assert {"201", "409", "422"} <= set(respostas)
