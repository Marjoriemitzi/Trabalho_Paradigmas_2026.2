import uuid

import pytest

from app.users.domain.repositories.refresh_token_repository import (
    RefreshTokenRepository,
)
from app.users.domain.value_objects.user_id import UserId
from tests.users.contracts.refresh_token_repository_contract import (
    RefreshTokenRepositoryContract,
)
from tests.users.fakes.fake_refresh_token_repository import FakeRefreshTokenRepository


class TestFakeRefreshTokenRepository(RefreshTokenRepositoryContract):
    @pytest.fixture
    def repository(self) -> RefreshTokenRepository:
        return FakeRefreshTokenRepository()

    @pytest.fixture
    def usuario(self) -> UserId:
        return UserId(uuid.uuid4())

    @pytest.fixture
    def outro_usuario(self) -> UserId:
        return UserId(uuid.uuid4())
