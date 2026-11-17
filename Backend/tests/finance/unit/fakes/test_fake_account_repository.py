import uuid

import pytest

from app.finance.domain.repositories.account_repository import AccountRepository
from app.finance.domain.value_objects.owner_id import OwnerId
from tests.finance.contracts.account_repository_contract import (
    AccountRepositoryContract,
)
from tests.finance.fakes.fake_account_repository import FakeAccountRepository


class TestFakeAccountRepository(AccountRepositoryContract):
    @pytest.fixture
    def repository(self) -> AccountRepository:
        return FakeAccountRepository()

    @pytest.fixture
    def dono(self) -> OwnerId:
        return OwnerId(uuid.uuid4())

    @pytest.fixture
    def outro_dono(self) -> OwnerId:
        return OwnerId(uuid.uuid4())
