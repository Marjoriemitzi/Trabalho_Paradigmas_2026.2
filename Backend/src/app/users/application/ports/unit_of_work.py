from types import TracebackType
from typing import Protocol, Self

from app.users.domain.repositories.refresh_token_repository import (
    RefreshTokenRepository,
)
from app.users.domain.repositories.user_repository import UserRepository


class UnitOfWork(Protocol):
    @property
    def users(self) -> UserRepository: ...

    @property
    def refresh_tokens(self) -> RefreshTokenRepository: ...

    async def __aenter__(self) -> Self: ...

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        tb: TracebackType | None,
    ) -> None: ...

    async def commit(self) -> None: ...
