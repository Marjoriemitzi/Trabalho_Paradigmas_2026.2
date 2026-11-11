from datetime import datetime
from typing import Protocol


class TokenBlocklistRepository(Protocol):
    async def add(self, token: str, expires_at: datetime) -> None:
        ...

    async def is_blocked(self, token: str) -> bool:
        ...
