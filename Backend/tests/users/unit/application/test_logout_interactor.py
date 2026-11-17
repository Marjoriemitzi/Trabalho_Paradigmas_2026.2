from datetime import UTC, datetime
import pytest
from app.users.application.use_cases.logout_interactor import LogoutInteractor
from app.users.application.use_cases.logout_user import LogoutUserRequest

class FakeTokenBlocklist:
    def __init__(self):
        self.added = False
        self.deleted = False

    async def add(self, jti, user_id, expires_at):
        self.added = True

    async def delete_expired(self, now):
        self.deleted = True

class FakeUOW:
    def __init__(self):
        self.token_blocklist = FakeTokenBlocklist()
        self.committed = False
    async def commit(self):
        self.committed = True

class SpyPresenter:
    def __init__(self):
        self.called = False
    def present_success(self):
        self.called = True

@pytest.mark.asyncio
async def test_logout_interactor():
    uow = FakeUOW()
    presenter = SpyPresenter()
    interactor = LogoutInteractor(uow, presenter)
    request = LogoutUserRequest(jti="test-jti", user_id="test-id", expires_at=datetime.now(UTC))
    
    await interactor.execute(request)
    
    assert uow.token_blocklist.added
    assert uow.token_blocklist.deleted
    assert uow.committed
    assert presenter.called
