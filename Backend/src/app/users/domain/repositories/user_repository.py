from typing import Protocol

from app.users.domain.entities.user import User
from app.users.domain.value_objects.email import Email


class UserRepository(Protocol):
    async def add(self, user: User) -> None: ...
    async def exists(self, email: Email) -> bool: ...
    async def get_by_email(self, email: Email) -> User | None: ...
