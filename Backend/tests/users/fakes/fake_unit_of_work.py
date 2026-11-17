class FakeRefreshTokenStore:
    def __init__(self) -> None:
        self.store = {}

    async def add(self, user_id, family_id, token_hash, expires_at):
        self.store[token_hash] = {
            "id": "1",
            "user_id": user_id,
            "family_id": family_id,
            "token_hash": token_hash,
            "expires_at": expires_at,
            "used_at": None,
            "revoked_at": None,
        }

    async def get_by_hash(self, token_hash):
        return self.store.get(token_hash)

    async def mark_used(self, token_id, now):
        pass

    async def revoke_family(self, family_id, now):
        pass

    async def delete_expired(self, now):
        pass


from types import TracebackType
from typing import Self

from tests.users.fakes.fake_user_repository import FakeUserRepository


class FakeUnitOfWork:
    def __init__(self, users: FakeUserRepository | None = None) -> None:
        self.refresh_tokens = None
        self.refresh_tokens = FakeRefreshTokenStore()
        self.users = users or FakeUserRepository()
        self.committed = False
        self.rolled_back = False

    async def __aenter__(self) -> Self:
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        tb: TracebackType | None,
    ) -> None:
        if exc is not None:
            self.rolled_back = True

    async def commit(self) -> None:
        self.committed = True
