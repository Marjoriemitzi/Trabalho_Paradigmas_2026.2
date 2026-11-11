from datetime import datetime
from typing import Protocol


class TokenBlocklistRepository(Protocol):
    async def add(self, token: str, expires_at: datetime) -> None:
        """Adiciona um token à lista de bloqueio com sua data de expiração."""
        ...

    async def is_blocked(self, token: str) -> bool:
        """Verifica se um token já foi revogado."""
        ...