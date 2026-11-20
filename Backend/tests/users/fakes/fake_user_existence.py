from app.users.domain.value_objects.user_id import UserId
from tests.users.fakes.fake_user_repository import FakeUserRepository


class FakeUserExistence:
    """Sem repositório, todo mundo existe; com repositório, só quem foi gravado."""

    def __init__(self, users: FakeUserRepository | None = None) -> None:
        self._users = users

    async def exists(self, user_id: UserId) -> bool:
        if self._users is None:
            return True
        return await self._users.get_by_id(user_id) is not None
