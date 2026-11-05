"""Teste de fumaça: prova que app, pytest e cobertura estão ligados."""

import importlib

import pytest
from fastapi.testclient import TestClient

import finance_manager.main
from finance_manager.main import app


def test_health() -> None:
    client = TestClient(app)
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


@pytest.mark.parametrize("path", ["/docs", "/redoc", "/openapi.json"])
def test_docs_disabled_by_default(monkeypatch: pytest.MonkeyPatch, path: str) -> None:
    monkeypatch.delenv("ENABLE_DOCS", raising=False)
    module = importlib.reload(finance_manager.main)
    assert TestClient(module.app).get(path).status_code == 404


def test_docs_enabled_with_flag(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("ENABLE_DOCS", "true")
    module = importlib.reload(finance_manager.main)
    assert TestClient(module.app).get("/openapi.json").status_code == 200
