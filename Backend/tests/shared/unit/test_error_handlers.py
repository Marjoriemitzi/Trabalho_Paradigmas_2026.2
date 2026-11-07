from collections.abc import AsyncIterator

import pytest
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient

from app.shared.presentation.api.error_handlers import install_error_handlers
from app.shared.presentation.api.errors import ApiError

app = FastAPI()
install_error_handlers(app)


@app.get("/protegida")
async def protegida() -> None:
    raise ApiError(401, "invalid_token", headers={"WWW-Authenticate": "Bearer"})


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
