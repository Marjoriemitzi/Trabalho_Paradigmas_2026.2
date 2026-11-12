from types import TracebackType
from typing import Protocol, Self

from app.finance.application.ports.spending_reader import SpendingReader
from app.finance.domain.repositories.account_repository import AccountRepository
from app.finance.domain.repositories.category_catalog import CategoryCatalog
from app.finance.domain.repositories.transaction_repository import (
    TransactionRepository,
)
from app.finance.domain.repositories.transfer_repository import TransferRepository


class UnitOfWork(Protocol):
    @property
    def accounts(self) -> AccountRepository: ...

    @property
    def categories(self) -> CategoryCatalog: ...

    @property
    def spending(self) -> SpendingReader: ...

    @property
    def transactions(self) -> TransactionRepository: ...

    @property
    def transfers(self) -> TransferRepository: ...

    async def __aenter__(self) -> Self: ...

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        tb: TracebackType | None,
    ) -> None: ...

    async def commit(self) -> None: ...
