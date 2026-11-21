import uuid

import pytest

from app.finance.domain.repositories.recurrence_repository import (
    RecurrenceRepository,
)
from app.finance.domain.value_objects.account_id import AccountId
from app.finance.domain.value_objects.owner_id import OwnerId
from tests.finance.contracts.recurrence_repository_contract import (
    RecurrenceRepositoryContract,
)
from tests.finance.fakes.fake_recurrence_repository import FakeRecurrenceRepository


class TestFakeRecurrenceRepository(RecurrenceRepositoryContract):
    @pytest.fixture
    def repository(self) -> RecurrenceRepository:
        return FakeRecurrenceRepository()

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
    def conta_do_outro(self) -> AccountId:
        return AccountId.new()
