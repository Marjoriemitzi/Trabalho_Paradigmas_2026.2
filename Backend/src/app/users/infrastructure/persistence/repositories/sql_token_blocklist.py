import uuid
from datetime import datetime

from sqlalchemy import delete, exists, select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession

from app.users.domain.value_objects.user_id import UserId
from app.users.infrastructure.persistence.models.revoked_token_model import (
    RevokedTokenModel,
)


class SqlTokenBlocklist:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def add(self, jti: uuid.UUID, user_id: UserId, expires_at: datetime) -> None:
        await self._session.execute(
            insert(RevokedTokenModel)
            .values(jti=jti, user_id=user_id.value, expires_at=expires_at)
            .on_conflict_do_nothing(index_elements=["jti"])
        )

    async def contains(self, jti: uuid.UUID) -> bool:
        consulta = select(exists().where(RevokedTokenModel.jti == jti))
        return bool(await self._session.scalar(consulta))

    async def delete_expired(self, now: datetime) -> None:
        await self._session.execute(
            delete(RevokedTokenModel).where(RevokedTokenModel.expires_at < now)
        )
