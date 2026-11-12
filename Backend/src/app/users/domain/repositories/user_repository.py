from typing import Protocol

from app.users.domain.entities.user import User
from app.users.domain.value_objects.email import Email
from app.users.domain.value_objects.user_id import UserId


class UserRepository(Protocol):
    async def add(self, user: User) -> None: ...

    async def exists(self, email: Email) -> bool: ...

    async def get_by_email(self, email: Email) -> User | None: ...

    async def get_by_id(self, user_id: UserId) -> User | None: ...
