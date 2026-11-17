from types import TracebackType
from typing import Protocol, Self

from app.users.domain.repositories.user_repository import UserRepository


class UnitOfWork(Protocol):
    @property
    def users(self) -> UserRepository: ...

    async def __aenter__(self) -> Self: ...

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        tb: TracebackType | None,
    ) -> None: ...

    async def commit(self) -> None: ...
