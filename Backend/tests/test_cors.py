from pathlib import Path

import pytest
from httpx import ASGITransport, AsyncClient
from pydantic import SecretStr

from app.main import create_app
from app.shared.infrastructure.config.settings import Settings


def cfg(origins: list[str]) -> Settings:
    return Settings(
        database_url=SecretStr("postgresql+asyncpg://u:s@localhost/finance"),
        prolog_rules_dir=Path("rules"),
        jwt_secret=SecretStr("s" * 32),
        cors_origins=origins,
    )


@pytest.mark.asyncio
async def test_preflight_origem_permitida():
    app = create_app(cfg(["http://localhost:8001"]))
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as ac:
        res = await ac.options(
            "/api/v1/accounts",
            headers={
                "Origin": "http://localhost:8001",
                "Access-Control-Request-Method": "POST",
                "Access-Control-Request-Headers": "authorization, content-type",
            },
        )
        assert res.status_code == 200
        assert res.headers["access-control-allow-origin"] == "http://localhost:8001"
        assert "POST" in res.headers["access-control-allow-methods"]
        assert (
            "authorization"
            in res.headers.get("access-control-allow-headers", "").lower()
        )


@pytest.mark.asyncio
async def test_preflight_origem_nao_permitida():
    app = create_app(cfg(["http://localhost:8001"]))
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as ac:
        res = await ac.options(
            "/api/v1/accounts",
            headers={
                "Origin": "http://malicious.com",
                "Access-Control-Request-Method": "POST",
            },
        )
        assert "access-control-allow-origin" not in res.headers


@pytest.mark.asyncio
async def test_sem_cors_nenhuma_resposta_traz_cabecalho():
    app = create_app(cfg([]))
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as ac:
        res = await ac.options(
            "/api/v1/accounts",
            headers={
                "Origin": "http://localhost:8001",
                "Access-Control-Request-Method": "POST",
            },
        )
        assert "access-control-allow-origin" not in res.headers


@pytest.mark.asyncio
async def test_get_health_expoe_retry_after():
    app = create_app(cfg(["http://localhost:8001"]))
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as ac:
        res = await ac.get("/health", headers={"Origin": "http://localhost:8001"})
        assert res.status_code == 200
        assert "access-control-allow-origin" in res.headers
        assert (
            "retry-after"
            in res.headers.get("access-control-expose-headers", "").lower()
        )
