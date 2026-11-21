import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.finance.application.ports.account_usage import AccountUsage
from app.finance.domain.repositories.account_repository import AccountRepository
from app.finance.domain.repositories.recurrence_repository import (
    RecurrenceRepository,
)
from app.finance.domain.repositories.transaction_repository import (
    TransactionRepository,
)
from app.finance.domain.repositories.transfer_repository import TransferRepository
from app.finance.domain.value_objects.owner_id import OwnerId
from app.finance.infrastructure.persistence.repositories.sql_account_repository import (
    SqlAccountRepository,
)
from app.finance.infrastructure.persistence.repositories.sql_account_usage import (
    SqlAccountUsage,
)
from app.finance.infrastructure.persistence.repositories.sql_recurrence_repository import (  # noqa: E501
    SqlRecurrenceRepository,
)
from app.finance.infrastructure.persistence.repositories.sql_transaction_repository import (  # noqa: E501
    SqlTransactionRepository,
)
from app.finance.infrastructure.persistence.repositories.sql_transfer_repository import (  # noqa: E501
    SqlTransferRepository,
)
from tests.finance.contracts.account_usage_contract import AccountUsageContract
from tests.finance.integration.conftest import NovoDono


class TestSqlAccountUsage(AccountUsageContract):
    @pytest.fixture
    def accounts(self, session: AsyncSession) -> AccountRepository:
        return SqlAccountRepository(session)

    @pytest.fixture
    def transactions(self, session: AsyncSession) -> TransactionRepository:
        return SqlTransactionRepository(session)

    @pytest.fixture
    def transfers(self, session: AsyncSession) -> TransferRepository:
        return SqlTransferRepository(session)

    @pytest.fixture
    def recurrences(self, session: AsyncSession) -> RecurrenceRepository:
        return SqlRecurrenceRepository(session)

    @pytest.fixture
    def usage(self, session: AsyncSession) -> AccountUsage:
        return SqlAccountUsage(session)

    @pytest.fixture
    async def dono(self, novo_dono: NovoDono) -> OwnerId:
        return await novo_dono()
