import uuid

import pytest

from app.users.application.ports.access_token_check import AccessTokenCheck
from app.users.domain.entities.user import User
from app.users.domain.value_objects.email import Email
from app.users.domain.value_objects.password import PasswordHash
from app.users.domain.value_objects.user_id import UserId
from tests.users.contracts.access_token_check_contract import (
    AccessTokenCheckContract,
    Bloquear,
)
from tests.users.fakes.authenticated import autenticado
from tests.users.fakes.fake_access_token_check import FakeAccessTokenCheck
from tests.users.fakes.fake_user_repository import FakeUserRepository


class TestFakeAccessTokenCheck(AccessTokenCheckContract):
    @pytest.fixture
    def users(self) -> FakeUserRepository:
        return FakeUserRepository()

    @pytest.fixture
    def fake(self, users: FakeUserRepository) -> FakeAccessTokenCheck:
        return FakeAccessTokenCheck(users)

    @pytest.fixture
    def check(self, fake: FakeAccessTokenCheck) -> AccessTokenCheck:
        return fake

    @pytest.fixture
    async def usuario(self, users: FakeUserRepository) -> UserId:
        user = User.register(Email("ana@acme.com"), PasswordHash("hash"))
        await users.add(user)
        return user.id

    @pytest.fixture
    def bloquear(self, fake: FakeAccessTokenCheck) -> Bloquear:
        async def _bloquear(jti: uuid.UUID, _usuario: UserId) -> None:
            fake.revoked.add(jti)

        return _bloquear


async def test_sem_repositorio_todo_usuario_existe() -> None:
    assert await FakeAccessTokenCheck().is_valid(autenticado(UserId.new())) is True
