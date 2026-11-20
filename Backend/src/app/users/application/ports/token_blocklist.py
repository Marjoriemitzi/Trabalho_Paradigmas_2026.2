import uuid
from datetime import datetime
from typing import Protocol

from app.users.domain.value_objects.user_id import UserId


class TokenBlocklist(Protocol):
    async def add(self, jti: uuid.UUID, user_id: UserId, expires_at: datetime) -> None:
        """Bloqueia o token até ele vencer. Repetir o mesmo jti não faz mal."""
        ...

    async def contains(self, jti: uuid.UUID) -> bool: ...

    async def delete_expired(self, now: datetime) -> None: ...
