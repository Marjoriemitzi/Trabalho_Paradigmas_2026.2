from fastapi.testclient import TestClient
from fastapi import Request
from app.main import app
from app.users.presentation.api.v1.security import require_authenticated_user
from app.users.application.ports.token_verifier import AuthenticatedUser
from datetime import UTC, datetime

client = TestClient(app)

async def override_auth(request: Request):
    return AuthenticatedUser(id="fake-id", role="user", jti="fake-jti", exp=datetime.now(UTC))

app.dependency_overrides[require_authenticated_user] = override_auth

def test_logout_endpoint():
    response = client.post("/api/v1/auth/logout")
    assert response.status_code == 204

def test_logout_without_token():
    app.dependency_overrides = {}
    response = client.post("/api/v1/auth/logout")
    assert response.status_code == 401
