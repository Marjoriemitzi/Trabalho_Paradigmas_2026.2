from types import TracebackType
from typing import Self

from tests.finance.fakes.fake_account_repository import FakeAccountRepository
from tests.finance.fakes.fake_category_catalog import FakeCategoryCatalog
from tests.finance.fakes.fake_spending_reader import FakeSpendingReader
from tests.finance.fakes.fake_transaction_repository import FakeTransactionRepository
from tests.finance.fakes.fake_transfer_repository import FakeTransferRepository


class FakeUnitOfWork:
    def __init__(self) -> None:
        self.accounts = FakeAccountRepository()
        self.categories = FakeCategoryCatalog()
        self.transactions = FakeTransactionRepository()
        self.spending = FakeSpendingReader(self.transactions)
        self.transfers = FakeTransferRepository()
        self.committed = False

    async def __aenter__(self) -> Self:
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        tb: TracebackType | None,
    ) -> None:
        return None

    async def commit(self) -> None:
        self.committed = True
