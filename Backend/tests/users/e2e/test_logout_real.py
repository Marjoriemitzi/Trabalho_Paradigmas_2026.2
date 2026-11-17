import pytest
from httpx import AsyncClient, ASGITransport
from app.main import create_app
from tests.users.e2e.conftest import create_fake_user, get_db_session

@pytest.mark.asyncio
async def test_logout_real_flow(test_client):
    app = create_app()
    async with get_db_session() as session:
        user = await create_fake_user(session, email="logout@test.com")
        
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        # Login
        login_data = {"email": "logout@test.com", "password": "TestPassword123!"}
        login_res = await ac.post("/api/v1/auth/login", json=login_data)
        assert login_res.status_code == 200
        token = login_res.json()["access_token"]
        
        headers = {"Authorization": f"Bearer {token}"}
        
        # Acesso permitido
        me_res = await ac.get("/api/v1/users/me", headers=headers)
        assert me_res.status_code == 200
        
        # Logout
        logout_res = await ac.post("/api/v1/auth/logout", headers=headers)
        assert logout_res.status_code == 204
        
        # Acesso negado
        me_res_after = await ac.get("/api/v1/users/me", headers=headers)
        assert me_res_after.status_code == 401
        assert me_res_after.json()["error"] == "invalid_token"
