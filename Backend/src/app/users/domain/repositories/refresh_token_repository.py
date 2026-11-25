import uuid
from datetime import datetime
from typing import Protocol

from app.users.domain.entities.refresh_token import RefreshToken
from app.users.domain.value_objects.user_id import UserId


class RefreshTokenRepository(Protocol):
    async def add(self, token: RefreshToken) -> None: ...

    async def get_by_hash(self, token_hash: str) -> RefreshToken | None: ...

    async def mark_used(self, token_id: uuid.UUID, now: datetime) -> bool:
        """Marca como usado só se ainda não foi usado nem revogado.

        Devolve False quando outro pedido chegou antes (ou o token foi revogado).
        """
        ...

    async def revoke_family(self, family_id: uuid.UUID, now: datetime) -> None: ...

    async def revoke_all_for_user(self, user_id: UserId, now: datetime) -> None:
        """Revoga todos os refresh tokens ainda não revogados do usuário."""
        ...

    async def delete_expired_before(self, limit: datetime) -> None: ...
