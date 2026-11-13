import uuid

import pytest

from app.finance.application.ports.spending_reader import SpendingReader
from app.finance.domain.repositories.transaction_repository import (
    TransactionRepository,
)
from app.finance.domain.value_objects.account_id import AccountId
from app.finance.domain.value_objects.owner_id import OwnerId
from tests.finance.contracts.spending_reader_contract import SpendingReaderContract
from tests.finance.fakes.fake_spending_reader import FakeSpendingReader
from tests.finance.fakes.fake_transaction_repository import FakeTransactionRepository


class TestFakeSpendingReader(SpendingReaderContract):
    @pytest.fixture
    def repository(self) -> FakeTransactionRepository:
        return FakeTransactionRepository()

    @pytest.fixture
    def reader(self, repository: TransactionRepository) -> SpendingReader:
        assert isinstance(repository, FakeTransactionRepository)
        return FakeSpendingReader(repository)

    @pytest.fixture
    def dono(self) -> OwnerId:
        return OwnerId(uuid.uuid4())

    @pytest.fixture
    def outro_dono(self) -> OwnerId:
        return OwnerId(uuid.uuid4())

    @pytest.fixture
    def conta(self) -> AccountId:
        return AccountId.new()

    @pytest.fixture
    def outra_conta(self) -> AccountId:
        return AccountId.new()

    @pytest.fixture
    def conta_do_outro(self) -> AccountId:
        return AccountId.new()
