from types import TracebackType
from typing import Self

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.users.domain.repositories.user_repository import UserRepository
from app.users.infrastructure.persistence.repositories.sql_user_repository import (
    SqlUserRepository,
)


class SqlAlchemyUnitOfWork:
    def __init__(self, session_factory: async_sessionmaker[AsyncSession]) -> None:
        self._session_factory = session_factory
        self._session: AsyncSession | None = None

    @property
    def users(self) -> UserRepository:
        return SqlUserRepository(self._open_session())

    async def __aenter__(self) -> Self:
        self._session = self._session_factory()
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        tb: TracebackType | None,
    ) -> None:
        await self._open_session().close()
        self._session = None

    async def commit(self) -> None:
        await self._open_session().commit()

    def _open_session(self) -> AsyncSession:
        if self._session is None:
            raise RuntimeError("Use a UnitOfWork dentro de um bloco 'async with'.")
        return self._session
