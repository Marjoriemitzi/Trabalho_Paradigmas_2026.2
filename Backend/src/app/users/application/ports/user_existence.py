from typing import Protocol

from app.users.domain.value_objects.user_id import UserId


class UserExistence(Protocol):
    async def exists(self, user_id: UserId) -> bool: ...
