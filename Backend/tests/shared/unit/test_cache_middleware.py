from fastapi import FastAPI, Response
from fastapi.testclient import TestClient

from app.shared.presentation.api.middleware import CacheControlMiddleware


def cliente() -> TestClient:
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

    return TestClient(app)


def test_rotas_da_api_levam_no_store() -> None:
    assert cliente().get("/api/v1/x").headers["cache-control"] == "no-store"


def test_o_catalogo_e_o_health_ficam_sem_o_cabecalho() -> None:
    http = cliente()

    assert "cache-control" not in http.get("/api/v1/categories").headers
    assert "cache-control" not in http.get("/health").headers


def test_a_rota_que_ja_define_o_cabecalho_mantem_o_valor() -> None:
    assert cliente().get("/api/v1/propria").headers["cache-control"] == "max-age=3600"
