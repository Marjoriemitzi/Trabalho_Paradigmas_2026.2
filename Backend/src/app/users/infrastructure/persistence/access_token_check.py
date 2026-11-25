from typing import override

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.users.application.ports.access_token_check import AccessTokenCheck
from app.users.application.ports.token_verifier import AuthenticatedUser
from app.users.infrastructure.persistence.unit_of_work import SqlAlchemyUnitOfWork


class SqlAccessTokenCheck(AccessTokenCheck):
    def __init__(self, session_factory: async_sessionmaker[AsyncSession]) -> None:
        self._session_factory = session_factory

    @override
    async def is_valid(self, current: AuthenticatedUser) -> bool:
        async with SqlAlchemyUnitOfWork(self._session_factory) as uow:
            if await uow.token_blocklist.contains(current.jti):
                return False
            return await uow.users.get_by_id(current.id) is not None
