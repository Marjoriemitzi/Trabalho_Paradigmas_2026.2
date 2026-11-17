from datetime import datetime
from typing import Protocol


class TokenBlocklist(Protocol):
    async def add(self, jti: str, user_id: str, expires_at: datetime) -> None: ...

    async def contains(self, jti: str) -> bool: ...

    async def delete_expired(self, now: datetime) -> None: ...
