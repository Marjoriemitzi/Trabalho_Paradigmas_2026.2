from pathlib import Path

import pytest
from fastapi.testclient import TestClient
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


def test_health() -> None:
    client = TestClient(create_app(configuracao(enable_docs=False)))
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


@pytest.mark.parametrize("path", ["/docs", "/redoc", "/openapi.json"])
def test_documentacao_desligada_por_padrao(path: str) -> None:
    client = TestClient(create_app(configuracao(enable_docs=False)))
    assert client.get(path).status_code == 404


def test_documentacao_ligada_quando_pedido() -> None:
    client = TestClient(create_app(configuracao(enable_docs=True)))
    assert client.get("/openapi.json").status_code == 200
