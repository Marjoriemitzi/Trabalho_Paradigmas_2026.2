"""
Contrato da porta UserRepository.
"""

import pytest

from app.users.domain.entities.user import User
from app.users.domain.repositories.user_repository import UserRepository
from app.users.domain.value_objects.email import Email
from app.users.domain.value_objects.password import PasswordHash

HASH = "$argon2id$v=19$m=65536,t=3,p=4$c2FsdA$aGFzaA"


class UserRepositoryContract:
    @pytest.fixture
    def repository(self) -> UserRepository:
        raise NotImplementedError

    async def test_email_desconhecido_nao_existe(
        self, repository: UserRepository
    ) -> None:
        assert await repository.exists(Email("ana@acme.com")) is False

    async def test_usuario_adicionado_passa_a_existir(
        self, repository: UserRepository
    ) -> None:
        user = User.register(Email("ana@acme.com"), PasswordHash(HASH))
        await repository.add(user)
        assert await repository.exists(Email("ana@acme.com")) is True

    async def test_encontra_o_email_escrito_de_outro_jeito(
        self, repository: UserRepository
    ) -> None:
        await repository.add(User.register(Email("ana@acme.com"), PasswordHash(HASH)))
        assert await repository.exists(Email("  ANA@Acme.com ")) is True
