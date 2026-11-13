from types import TracebackType
from typing import Self

from tests.users.fakes.fake_user_repository import FakeUserRepository


class FakeUnitOfWork:
    def __init__(self, users: FakeUserRepository | None = None) -> None:
        self.users = users or FakeUserRepository()
        self.committed = False
        self.rolled_back = False

    async def __aenter__(self) -> Self:
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        tb: TracebackType | None,
    ) -> None:
        if exc is not None:
            self.rolled_back = True

    async def commit(self) -> None:
        self.committed = True
