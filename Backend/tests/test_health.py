from pathlib import Path

import pytest
from httpx import ASGITransport, AsyncClient
from pydantic import SecretStr

from app.main import create_app
from app.shared.infrastructure.config.settings import Settings


def configuracao(*, enable_docs: bool) -> Settings:
    return Settings(
        database_url=SecretStr("postgresql+asyncpg://u:s@localhost/finance"),
        prolog_rules_dir=Path("rules"),
        jwt_secret=SecretStr("s" * 32),
        enable_docs=enable_docs,
    )


def cliente(*, enable_docs: bool) -> AsyncClient:
    app = create_app(configuracao(enable_docs=enable_docs))
    return AsyncClient(transport=ASGITransport(app=app), base_url="http://teste")


async def test_health() -> None:
    async with cliente(enable_docs=False) as client:
        response = await client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


@pytest.mark.parametrize("path", ["/docs", "/redoc", "/openapi.json"])
async def test_documentacao_desligada_por_padrao(path: str) -> None:
    async with cliente(enable_docs=False) as client:
        assert (await client.get(path)).status_code == 404


async def test_documentacao_ligada_quando_pedido() -> None:
    async with cliente(enable_docs=True) as client:
        assert (await client.get("/openapi.json")).status_code == 200


async def test_a_aplicacao_responde_erros_no_formato_unico() -> None:
    async with cliente(enable_docs=False) as client:
        resposta = await client.get("/nao-existe")

    assert resposta.status_code == 404
    assert resposta.json() == {"error": "not_found"}
