import uuid
from datetime import datetime

from sqlalchemy import delete, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.users.domain.entities.refresh_token import RefreshToken
from app.users.domain.value_objects.user_id import UserId
from app.users.infrastructure.persistence.models.refresh_token_model import (
    RefreshTokenModel,
)


def _to_entity(modelo: RefreshTokenModel) -> RefreshToken:
    return RefreshToken(
        id=modelo.id,
        user_id=UserId(modelo.user_id),
        family_id=modelo.family_id,
        token_hash=modelo.token_hash,
        expires_at=modelo.expires_at,
        used_at=modelo.used_at,
        revoked_at=modelo.revoked_at,
    )


class SqlRefreshTokenRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def add(self, token: RefreshToken) -> None:
        self._session.add(
            RefreshTokenModel(
                id=token.id,
                user_id=token.user_id.value,
                family_id=token.family_id,
                token_hash=token.token_hash,
                expires_at=token.expires_at,
                used_at=token.used_at,
                revoked_at=token.revoked_at,
            )
        )
        await self._session.flush()

    async def get_by_hash(self, token_hash: str) -> RefreshToken | None:
        modelo = await self._session.scalar(
            select(RefreshTokenModel).where(RefreshTokenModel.token_hash == token_hash)
        )
        return None if modelo is None else _to_entity(modelo)

    async def mark_used(self, token_id: uuid.UUID, now: datetime) -> bool:
        marcado = await self._session.scalar(
            update(RefreshTokenModel)
            .where(
                RefreshTokenModel.id == token_id,
                RefreshTokenModel.used_at.is_(None),
                RefreshTokenModel.revoked_at.is_(None),
            )
            .values(used_at=now)
            .returning(RefreshTokenModel.id)
        )
        return marcado is not None

    async def revoke_family(self, family_id: uuid.UUID, now: datetime) -> None:
        await self._session.execute(
            update(RefreshTokenModel)
            .where(
                RefreshTokenModel.family_id == family_id,
                RefreshTokenModel.revoked_at.is_(None),
            )
            .values(revoked_at=now)
        )

    async def revoke_all_for_user(self, user_id: UserId, now: datetime) -> None:
        await self._session.execute(
            update(RefreshTokenModel)
            .where(
                RefreshTokenModel.user_id == user_id.value,
                RefreshTokenModel.revoked_at.is_(None),
            )
            .values(revoked_at=now)
        )

    async def delete_expired_before(self, limit: datetime) -> None:
        await self._session.execute(
            delete(RefreshTokenModel).where(RefreshTokenModel.expires_at < limit)
        )
