import pytest
from httpx import ASGITransport, AsyncClient

from app.main import create_app
from tests.users.e2e.conftest import create_fake_user, get_db_session


@pytest.mark.asyncio
async def test_delete_user_real_flow(test_client):
    app = create_app()
    async with get_db_session() as session:
        user = await create_fake_user(session, email="delete@test.com")

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as ac:
        login_res = await ac.post(
            "/api/v1/auth/login",
            json={"email": "delete@test.com", "password": "TestPassword123!"},
        )
        token = login_res.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}

        # Sucesso
        res = await ac.request(
            "DELETE",
            "/api/v1/users/me",
            json={"password": "TestPassword123!"},
            headers=headers,
        )
        assert res.status_code == 204

        # Novo acesso negado, pois consulta o banco
        me_res = await ac.get("/api/v1/users/me", headers=headers)
        assert me_res.status_code == 401
