from pathlib import Path

from httpx import ASGITransport, AsyncClient
from pydantic import SecretStr

from app.main import create_app
from app.shared.infrastructure.config.settings import Settings

ORIGEM = "http://localhost:8001"


def client(origens: list[str]) -> AsyncClient:
    settings = Settings(
        database_url=SecretStr("postgresql+asyncpg://u:s@localhost/finance"),
        prolog_rules_dir=Path("rules"),
        jwt_secret=SecretStr("s" * 32),
        cors_origins=origens,
    )
    transport = ASGITransport(app=create_app(settings))
    return AsyncClient(transport=transport, base_url="http://teste")


PREFLIGHT = {
    "Access-Control-Request-Method": "POST",
    "Access-Control-Request-Headers": "authorization, content-type",
}


async def test_preflight_de_origem_permitida_passa() -> None:
    async with client([ORIGEM]) as http:
        resposta = await http.options(
            "/api/v1/accounts", headers={"Origin": ORIGEM, **PREFLIGHT}
        )

    assert resposta.status_code == 200
    assert resposta.headers["access-control-allow-origin"] == ORIGEM
    assert "POST" in resposta.headers["access-control-allow-methods"]
    assert "authorization" in resposta.headers["access-control-allow-headers"].lower()


async def test_preflight_de_origem_nao_permitida_e_recusado() -> None:
    async with client([ORIGEM]) as http:
        resposta = await http.options(
            "/api/v1/accounts", headers={"Origin": "http://malvada.com", **PREFLIGHT}
        )

    assert resposta.status_code == 400
    assert "access-control-allow-origin" not in resposta.headers


async def test_sem_origens_configuradas_nao_ha_cors() -> None:
    async with client([]) as http:
        resposta = await http.get("/health", headers={"Origin": ORIGEM})

    assert resposta.status_code == 200
    assert "access-control-allow-origin" not in resposta.headers


async def test_pedido_simples_com_origem_permitida_expoe_retry_after() -> None:
    async with client([ORIGEM]) as http:
        resposta = await http.get("/health", headers={"Origin": ORIGEM})

    assert resposta.headers["access-control-allow-origin"] == ORIGEM
    assert "Retry-After" in resposta.headers["access-control-expose-headers"]
