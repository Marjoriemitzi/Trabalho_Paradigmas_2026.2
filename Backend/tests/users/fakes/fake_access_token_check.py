import uuid

from app.users.application.ports.token_verifier import AuthenticatedUser
from tests.users.fakes.fake_user_repository import FakeUserRepository


class FakeAccessTokenCheck:
    """Sem repositório, todo usuário existe; com repositório, só quem foi gravado."""

    def __init__(self, users: FakeUserRepository | None = None) -> None:
        self._users = users
        self.revoked: set[uuid.UUID] = set()

    async def is_valid(self, current: AuthenticatedUser) -> bool:
        if current.jti in self.revoked:
            return False
        if self._users is None:
            return True
        return await self._users.get_by_id(current.id) is not None
