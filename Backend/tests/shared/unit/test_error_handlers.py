from collections.abc import AsyncIterator

import pytest
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient
from pydantic import BaseModel, ConfigDict, SecretStr

from app.shared.presentation.api.error_handlers import install_error_handlers
from app.shared.presentation.api.errors import ApiError

app = FastAPI()
install_error_handlers(app)


@app.get("/protegida")
async def protegida() -> None:
    raise ApiError(401, "invalid_token", headers={"WWW-Authenticate": "Bearer"})


class Pedido(BaseModel):
    model_config = ConfigDict(extra="forbid")

    email: str
    password: SecretStr


@app.post("/pedido")
async def pedido(body: Pedido) -> None:
    return None


@pytest.fixture
async def client() -> AsyncIterator[AsyncClient]:
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://teste") as client:
        yield client


async def test_erro_levantado_numa_rota_sai_no_formato_unico(
    client: AsyncClient,
) -> None:
    resposta = await client.get("/protegida")

    assert resposta.status_code == 401
    assert resposta.json() == {"error": "invalid_token"}
    assert resposta.headers["www-authenticate"] == "Bearer"


async def test_rota_que_nao_existe_sai_no_formato_unico(client: AsyncClient) -> None:
    resposta = await client.get("/nao-existe")

    assert resposta.status_code == 404
    assert resposta.json() == {"error": "not_found"}


async def test_metodo_nao_permitido_sai_no_formato_unico(client: AsyncClient) -> None:
    resposta = await client.post("/protegida")

    assert resposta.status_code == 405
    assert resposta.json() == {"error": "method_not_allowed"}


async def test_sem_os_tratadores_o_status_continua_certo() -> None:
    sem_tratadores = FastAPI()
    sem_tratadores.add_api_route("/protegida", protegida)
    transport = ASGITransport(app=sem_tratadores)
    async with AsyncClient(transport=transport, base_url="http://teste") as client:
        resposta = await client.get("/protegida")

    assert resposta.status_code == 401


async def test_pedido_invalido_diz_o_problema_de_cada_campo(
    client: AsyncClient,
) -> None:
    resposta = await client.post(
        "/pedido", json={"email": "ana@acme.com", "senha": "S3nha!Forte123"}
    )

    assert resposta.status_code == 422
    assert resposta.json() == {
        "error": "invalid_request",
        "fields": [
            {"field": "password", "problem": "missing"},
            {"field": "senha", "problem": "extra_forbidden"},
        ],
    }


async def test_json_quebrado_nao_aponta_campo_nenhum(client: AsyncClient) -> None:
    resposta = await client.post(
        "/pedido", content='{"email":', headers={"Content-Type": "application/json"}
    )

    assert resposta.status_code == 422
    assert resposta.json() == {
        "error": "invalid_request",
        "fields": [{"field": None, "problem": "json_invalid"}],
    }


async def test_corpo_que_nao_e_objeto_nao_aponta_campo_nenhum(
    client: AsyncClient,
) -> None:
    resposta = await client.post("/pedido", json=["ana@acme.com", "S3nha!Forte123"])

    assert resposta.status_code == 422
    assert resposta.json() == {
        "error": "invalid_request",
        "fields": [{"field": None, "problem": "model_attributes_type"}],
    }
    assert "S3nha" not in resposta.text
