import uuid

import pytest

from app.finance.domain.repositories.transaction_repository import (
    TransactionRepository,
)
from app.finance.domain.value_objects.account_id import AccountId
from app.finance.domain.value_objects.owner_id import OwnerId
from tests.finance.contracts.transaction_repository_contract import (
    TransactionRepositoryContract,
)
from tests.finance.fakes.fake_transaction_repository import FakeTransactionRepository


class TestFakeTransactionRepository(TransactionRepositoryContract):
    @pytest.fixture
    def repository(self) -> TransactionRepository:
        return FakeTransactionRepository()

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
