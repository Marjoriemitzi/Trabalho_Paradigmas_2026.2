"""
Roda o contrato do UserRepository contra o fake em memória.
"""

import pytest

from app.users.domain.repositories.user_repository import UserRepository
from tests.users.contracts.user_repository_contract import UserRepositoryContract
from tests.users.fakes.fake_user_repository import FakeUserRepository


class TestFakeUserRepository(UserRepositoryContract):
    @pytest.fixture
    def repository(self) -> UserRepository:
        return FakeUserRepository()
