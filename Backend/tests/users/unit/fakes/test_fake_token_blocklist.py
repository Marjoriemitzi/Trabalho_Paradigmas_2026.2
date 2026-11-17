import pytest
from datetime import UTC, datetime, timedelta
from app.users.application.ports.token_blocklist import TokenBlocklist

class FakeTokenBlocklist(TokenBlocklist):
    def __init__(self):
        self._store = {}
    async def add(self, jti, user_id, expires_at):
        self._store[jti] = expires_at
    async def contains(self, jti):
        return jti in self._store
    async def delete_expired(self, now):
        self._store = {k: v for k, v in self._store.items() if v >= now}

@pytest.mark.asyncio
async def test_fake_token_blocklist():
    blocklist = FakeTokenBlocklist()
    now = datetime.now(UTC)
    await blocklist.add("jti-1", "user-1", now + timedelta(days=1))
    await blocklist.add("jti-2", "user-1", now - timedelta(days=1))
    
    assert await blocklist.contains("jti-1")
    await blocklist.delete_expired(now)
    assert not await blocklist.contains("jti-2")
