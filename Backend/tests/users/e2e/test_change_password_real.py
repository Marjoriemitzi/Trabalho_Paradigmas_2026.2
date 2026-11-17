import pytest
from httpx import ASGITransport, AsyncClient

from app.main import create_app
from tests.users.e2e.conftest import create_fake_user, get_db_session


@pytest.mark.asyncio
async def test_change_password_real_flow(test_client):
    app = create_app()
    async with get_db_session() as session:
        user = await create_fake_user(session, email="change@test.com")

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as ac:
        login_res = await ac.post(
            "/api/v1/auth/login",
            json={"email": "change@test.com", "password": "TestPassword123!"},
        )
        token = login_res.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}

        # Senha atual errada
        res1 = await ac.post(
            "/api/v1/users/me/password",
            json={
                "current_password": "WrongPassword123!",
                "new_password": "NewStrong123!",
            },
            headers=headers,
        )
        assert res1.status_code == 422
        assert res1.json()["error"] == "invalid_current_password"

        # Sucesso
        res2 = await ac.post(
            "/api/v1/users/me/password",
            json={
                "current_password": "TestPassword123!",
                "new_password": "NewStrongPassword123!",
            },
            headers=headers,
        )
        assert res2.status_code == 204

        # Login com senha nova
        login_res2 = await ac.post(
            "/api/v1/auth/login",
            json={"email": "change@test.com", "password": "NewStrongPassword123!"},
        )
        assert login_res2.status_code == 200
