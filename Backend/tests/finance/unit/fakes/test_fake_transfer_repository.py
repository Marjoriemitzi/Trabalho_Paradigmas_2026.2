import uuid

import pytest

from app.finance.domain.repositories.transfer_repository import TransferRepository
from app.finance.domain.value_objects.account_id import AccountId
from app.finance.domain.value_objects.owner_id import OwnerId
from tests.finance.contracts.transfer_repository_contract import (
    TransferRepositoryContract,
)
from tests.finance.fakes.fake_transfer_repository import FakeTransferRepository


class TestFakeTransferRepository(TransferRepositoryContract):
    @pytest.fixture
    def repository(self) -> TransferRepository:
        return FakeTransferRepository()

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
    def terceira_conta(self) -> AccountId:
        return AccountId.new()

    @pytest.fixture
    def contas_do_outro(self) -> tuple[AccountId, AccountId]:
        return AccountId.new(), AccountId.new()
