from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.users.domain.value_objects.user_id import UserId
from app.users.infrastructure.persistence.unit_of_work import SqlAlchemyUnitOfWork


class SqlUserExistence:
    def __init__(self, session_factory: async_sessionmaker[AsyncSession]) -> None:
        self._session_factory = session_factory

    async def exists(self, user_id: UserId) -> bool:
        async with SqlAlchemyUnitOfWork(self._session_factory) as uow:
            return await uow.users.get_by_id(user_id) is not None
