from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.shared.presentation.api.middleware import CacheControlMiddleware

app = FastAPI()
app.add_middleware(CacheControlMiddleware)


@app.get("/api/v1/test")
def test_route():
    return {"msg": "ok"}


@app.get("/api/v1/categories")
def test_categories():
    return {"msg": "ok"}


@app.get("/health")
def test_health():
    return {"msg": "ok"}


@app.get("/api/v1/custom")
def test_custom():
    from fastapi import Response

    return Response(headers={"Cache-Control": "max-age=3600"})


client = TestClient(app)


def test_cache_control_no_store_on_v1():
    res = client.get("/api/v1/test")
    assert res.headers.get("cache-control") == "no-store"


def test_no_cache_control_on_categories_and_health():
    assert "cache-control" not in client.get("/api/v1/categories").headers
    assert "cache-control" not in client.get("/health").headers


def test_preserves_existing_cache_control():
    res = client.get("/api/v1/custom")
    assert res.headers.get("cache-control") == "max-age=3600"
