from app.finance.application.ports.spending_reader import SpendingReader
from app.finance.domain.repositories.account_repository import AccountRepository
from app.finance.domain.repositories.category_catalog import CategoryCatalog
from app.finance.domain.repositories.transaction_repository import (
    TransactionRepository,
)
from app.finance.domain.repositories.transfer_repository import TransferRepository
from app.finance.infrastructure.persistence.repositories.sql_account_repository import (
    SqlAccountRepository,
)
from app.finance.infrastructure.persistence.repositories.sql_category_catalog import (
    SqlCategoryCatalog,
)
from app.finance.infrastructure.persistence.repositories.sql_spending_reader import (
    SqlSpendingReader,
)
from app.finance.infrastructure.persistence.repositories.sql_transaction_repository import (  # noqa: E501
    SqlTransactionRepository,
)
from app.finance.infrastructure.persistence.repositories.sql_transfer_repository import (  # noqa: E501
    SqlTransferRepository,
)
from app.shared.infrastructure.persistence.unit_of_work import (
    BaseSqlAlchemyUnitOfWork,
)


class SqlAlchemyUnitOfWork(BaseSqlAlchemyUnitOfWork):
    @property
    def accounts(self) -> AccountRepository:
        return SqlAccountRepository(self._open_session())

    @property
    def categories(self) -> CategoryCatalog:
        return SqlCategoryCatalog(self._open_session())

    @property
    def spending(self) -> SpendingReader:
        return SqlSpendingReader(self._open_session())

    @property
    def transactions(self) -> TransactionRepository:
        return SqlTransactionRepository(self._open_session())

    @property
    def transfers(self) -> TransferRepository:
        return SqlTransferRepository(self._open_session())
