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
from app.finance.application.use_cases.delete_account import (
    DeleteAccountInputPort,
    DeleteAccountInteractor,
    DeleteAccountOutputPort,
)
from app.finance.application.use_cases.rename_account import (
    RenameAccountInputPort,
    RenameAccountInteractor,
    RenameAccountOutputPort,
)
from app.finance.presentation.api.v1.routers.accounts import router
from app.shared.presentation.api.error_handlers import install_error_handlers
from tests.finance.fakes.fake_unit_of_work import FakeUnitOfWork
from tests.users.fakes.fake_token_verifier import FakeTokenVerifier
from tests.users.fakes.fake_user_existence import FakeUserExistence

URL = "/api/v1/accounts"
ANA, BIA = uuid.uuid4(), uuid.uuid4()


def token(pessoa: uuid.UUID) -> dict[str, str]:
    return {"Authorization": f"Bearer token-falso:{pessoa}"}


@pytest.fixture
async def client() -> AsyncIterator[AsyncClient]:
    uow = FakeUnitOfWork()

    def criar(presenter: CreateAccountOutputPort) -> CreateAccountInputPort:
        return CreateAccountInteractor(uow=uow, presenter=presenter)

    def renomear(presenter: RenameAccountOutputPort) -> RenameAccountInputPort:
        return RenameAccountInteractor(uow=uow, presenter=presenter)

    def apagar(presenter: DeleteAccountOutputPort) -> DeleteAccountInputPort:
        return DeleteAccountInteractor(uow=uow, presenter=presenter)

    app = FastAPI()
    install_error_handlers(app)
    app.include_router(router)
    app.state.create_account = criar
    app.state.rename_account = renomear
    app.state.delete_account = apagar
    app.state.token_verifier = FakeTokenVerifier()
    app.state.user_existence = FakeUserExistence()

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://teste") as client:
        yield client


async def abrir(client: AsyncClient, nome: str, dono: uuid.UUID = ANA) -> str:
    resposta = await client.post(
        URL, json={"name": nome, "kind": "checking"}, headers=token(dono)
    )
    return str(resposta.json()["id"])


async def test_renomear_responde_200_com_a_conta(client: AsyncClient) -> None:
    conta = await abrir(client, "Nubank")

    resposta = await client.patch(
        f"{URL}/{conta}", json={"name": "Conta do banco"}, headers=token(ANA)
    )

    assert resposta.status_code == 200
    assert resposta.json() == {
        "id": conta,
        "name": "Conta do banco",
        "kind": "checking",
    }


async def test_nome_repetido_responde_409(client: AsyncClient) -> None:
    await abrir(client, "Nubank")
    carteira = await abrir(client, "Carteira")

    resposta = await client.patch(
        f"{URL}/{carteira}", json={"name": "nubank"}, headers=token(ANA)
    )

    assert resposta.status_code == 409
    assert resposta.json() == {"error": "account_name_taken"}


async def test_nome_vazio_responde_422_invalid_account(client: AsyncClient) -> None:
    conta = await abrir(client, "Nubank")

    resposta = await client.patch(
        f"{URL}/{conta}", json={"name": " "}, headers=token(ANA)
    )

    assert resposta.status_code == 422
    assert resposta.json()["error"] == "invalid_account"


async def test_enviar_o_tipo_no_patch_responde_422_invalid_request(
    client: AsyncClient,
) -> None:
    conta = await abrir(client, "Nubank")

    resposta = await client.patch(
        f"{URL}/{conta}", json={"name": "X", "kind": "wallet"}, headers=token(ANA)
    )

    assert resposta.status_code == 422
    assert resposta.json()["error"] == "invalid_request"


async def test_id_que_nao_e_uuid_responde_422(client: AsyncClient) -> None:
    resposta = await client.patch(
        f"{URL}/nao-e-uuid", json={"name": "X"}, headers=token(ANA)
    )

    assert resposta.status_code == 422
    assert resposta.json()["error"] == "invalid_request"


async def test_conta_de_outra_pessoa_responde_404(client: AsyncClient) -> None:
    conta = await abrir(client, "Nubank")

    renomear = await client.patch(
        f"{URL}/{conta}", json={"name": "X"}, headers=token(BIA)
    )
    apagar = await client.delete(f"{URL}/{conta}", headers=token(BIA))

    assert renomear.status_code == apagar.status_code == 404
    assert renomear.json() == apagar.json() == {"error": "account_not_found"}


async def test_apagar_responde_204(client: AsyncClient) -> None:
    conta = await abrir(client, "Nubank")

    resposta = await client.delete(f"{URL}/{conta}", headers=token(ANA))

    assert resposta.status_code == 204


async def test_sem_token_responde_401(client: AsyncClient) -> None:
    conta = uuid.uuid4()

    renomear = await client.patch(f"{URL}/{conta}", json={"name": "X"})
    apagar = await client.delete(f"{URL}/{conta}")

    assert renomear.status_code == apagar.status_code == 401
