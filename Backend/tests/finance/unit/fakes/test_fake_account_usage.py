import uuid

import pytest

from app.finance.application.ports.account_usage import AccountUsage
from app.finance.domain.repositories.account_repository import AccountRepository
from app.finance.domain.value_objects.owner_id import OwnerId
from tests.finance.contracts.account_usage_contract import AccountUsageContract
from tests.finance.fakes.fake_account_repository import FakeAccountRepository
from tests.finance.fakes.fake_account_usage import FakeAccountUsage
from tests.finance.fakes.fake_transaction_repository import FakeTransactionRepository
from tests.finance.fakes.fake_transfer_repository import FakeTransferRepository


class TestFakeAccountUsage(AccountUsageContract):
    @pytest.fixture
    def accounts(self) -> AccountRepository:
        return FakeAccountRepository()

    @pytest.fixture
    def transactions(self) -> FakeTransactionRepository:
        return FakeTransactionRepository()

    @pytest.fixture
    def transfers(self) -> FakeTransferRepository:
        return FakeTransferRepository()

    @pytest.fixture
    def usage(
        self, transactions: FakeTransactionRepository, transfers: FakeTransferRepository
    ) -> AccountUsage:
        return FakeAccountUsage(transactions, transfers)

    @pytest.fixture
    def dono(self) -> OwnerId:
        return OwnerId(uuid.uuid4())
