import uuid
from datetime import datetime

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.users.application.ports.token_blocklist import TokenBlocklist
from app.users.infrastructure.persistence.models.revoked_token_model import (
    RevokedTokenModel,
)


class SqlTokenBlocklist(TokenBlocklist):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def add(self, jti: str, user_id: str, expires_at: datetime) -> None:
        model = RevokedTokenModel(
            jti=uuid.UUID(jti),
            user_id=uuid.UUID(user_id),
            expires_at=expires_at,
        )
        self._session.add(model)

    async def contains(self, jti: str) -> bool:
        stmt = select(RevokedTokenModel).where(RevokedTokenModel.jti == uuid.UUID(jti))
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none() is not None

    async def delete_expired(self, now: datetime) -> None:
        stmt = delete(RevokedTokenModel).where(RevokedTokenModel.expires_at < now)
        await self._session.execute(stmt)
