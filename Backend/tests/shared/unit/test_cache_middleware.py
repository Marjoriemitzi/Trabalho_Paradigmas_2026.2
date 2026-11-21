from fastapi import FastAPI, Response
from httpx import ASGITransport, AsyncClient

from app.shared.presentation.api.middleware import CacheControlMiddleware


def cliente() -> AsyncClient:
    app = FastAPI()
    app.add_middleware(CacheControlMiddleware)

    @app.get("/api/v1/x")
    def rota() -> dict[str, str]:
        return {"msg": "ok"}

    @app.get("/api/v1/categories")
    def categorias() -> dict[str, str]:
        return {"msg": "ok"}

    @app.get("/health")
    def saude() -> dict[str, str]:
        return {"msg": "ok"}

    @app.get("/api/v1/propria")
    def propria(resposta: Response) -> dict[str, str]:
        resposta.headers["Cache-Control"] = "max-age=3600"
        return {"msg": "ok"}

    return AsyncClient(transport=ASGITransport(app=app), base_url="http://teste")


async def test_rotas_da_api_levam_no_store() -> None:
    async with cliente() as http:
        resposta = await http.get("/api/v1/x")

    assert resposta.headers["cache-control"] == "no-store"


async def test_o_catalogo_e_o_health_ficam_sem_o_cabecalho() -> None:
    async with cliente() as http:
        categorias = await http.get("/api/v1/categories")
        saude = await http.get("/health")

    assert "cache-control" not in categorias.headers
    assert "cache-control" not in saude.headers


async def test_a_rota_que_ja_define_o_cabecalho_mantem_o_valor() -> None:
    async with cliente() as http:
        resposta = await http.get("/api/v1/propria")

    assert resposta.headers["cache-control"] == "max-age=3600"
