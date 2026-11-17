from datetime import datetime

from sqlalchemy import delete, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.users.infrastructure.persistence.models.refresh_token_model import (
    RefreshTokenModel,
)


class SqlRefreshTokenStore:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def add(
        self, user_id: str, family_id: str, token_hash: str, expires_at: datetime
    ) -> None:
        self._session.add(
            RefreshTokenModel(
                user_id=user_id,
                family_id=family_id,
                token_hash=token_hash,
                expires_at=expires_at,
            )
        )
        await self._session.flush()

    async def get_by_hash(self, token_hash: str) -> dict[str, object] | None:
        modelo = await self._session.scalar(
            select(RefreshTokenModel).where(RefreshTokenModel.token_hash == token_hash)
        )
        if not modelo:
            return None
        return {
            "id": str(modelo.id),
            "user_id": str(modelo.user_id),
            "family_id": str(modelo.family_id),
            "token_hash": modelo.token_hash,
            "expires_at": modelo.expires_at,
            "used_at": modelo.used_at,
            "revoked_at": modelo.revoked_at,
        }

    async def mark_used(self, token_id: str, now: datetime) -> None:
        await self._session.execute(
            update(RefreshTokenModel)
            .where(RefreshTokenModel.id == token_id)
            .values(used_at=now)
        )
        await self._session.flush()

    async def revoke_family(self, family_id: str, now: datetime) -> None:
        await self._session.execute(
            update(RefreshTokenModel)
            .where(RefreshTokenModel.family_id == family_id)
            .where(RefreshTokenModel.revoked_at == None)
            .values(revoked_at=now)
        )
        await self._session.flush()

    async def delete_expired(self, now: datetime) -> None:
        await self._session.execute(
            delete(RefreshTokenModel).where(RefreshTokenModel.expires_at < now)
        )
        await self._session.flush()
