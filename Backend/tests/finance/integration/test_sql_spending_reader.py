import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.finance.application.ports.spending_reader import SpendingReader
from app.finance.domain.repositories.transaction_repository import (
    TransactionRepository,
)
from app.finance.domain.value_objects.account_id import AccountId
from app.finance.domain.value_objects.owner_id import OwnerId
from app.finance.infrastructure.persistence.repositories.sql_spending_reader import (
    SqlSpendingReader,
)
from app.finance.infrastructure.persistence.repositories.sql_transaction_repository import (  # noqa: E501
    SqlTransactionRepository,
)
from tests.finance.contracts.spending_reader_contract import SpendingReaderContract
from tests.finance.integration.conftest import NovaConta, NovoDono


class TestSqlSpendingReader(SpendingReaderContract):
    @pytest.fixture
    def repository(self, session: AsyncSession) -> TransactionRepository:
        return SqlTransactionRepository(session)

    @pytest.fixture
    def reader(
        self, repository: TransactionRepository, session: AsyncSession
    ) -> SpendingReader:
        return SqlSpendingReader(session)

    @pytest.fixture
    async def dono(self, novo_dono: NovoDono) -> OwnerId:
        return await novo_dono()

    @pytest.fixture
    async def outro_dono(self, novo_dono: NovoDono) -> OwnerId:
        return await novo_dono()

    @pytest.fixture
    async def conta(self, nova_conta: NovaConta, dono: OwnerId) -> AccountId:
        return await nova_conta(dono)

    @pytest.fixture
    async def outra_conta(self, nova_conta: NovaConta, dono: OwnerId) -> AccountId:
        return await nova_conta(dono)

    @pytest.fixture
    async def conta_do_outro(
        self, nova_conta: NovaConta, outro_dono: OwnerId
    ) -> AccountId:
        return await nova_conta(outro_dono)
