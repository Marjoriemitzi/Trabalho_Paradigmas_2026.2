"""Fake em memória da porta UserRepository."""

from app.users.domain.entities.user import User
from app.users.domain.value_objects.email import Email


class FakeUserRepository:
    def __init__(self) -> None:
        self._by_email: dict[Email, User] = {}

    async def add(self, user: User) -> None:
        self._by_email[user.email] = user

    async def exists(self, email: Email) -> bool:
        return email in self._by_email
