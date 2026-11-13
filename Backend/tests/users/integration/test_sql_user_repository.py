import pytest
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.users.domain.entities.user import User
from app.users.domain.repositories.user_repository import UserRepository
from app.users.domain.value_objects.email import Email
from app.users.domain.value_objects.password import PasswordHash
from app.users.infrastructure.persistence.models.user_model import UserModel
from app.users.infrastructure.persistence.repositories.sql_user_repository import (
    SqlUserRepository,
)
from tests.users.contracts.user_repository_contract import (
    HASH,
    UserRepositoryContract,
)


class TestSqlUserRepository(UserRepositoryContract):
    @pytest.fixture
    def repository(self, session: AsyncSession) -> UserRepository:
        return SqlUserRepository(session)


async def test_grava_cada_campo_na_sua_coluna(session: AsyncSession) -> None:
    user = User.register(Email("Ana@Acme.com"), PasswordHash(HASH))
    await SqlUserRepository(session).add(user)

    linha = await session.scalar(select(UserModel).where(UserModel.id == user.id.value))

    assert linha is not None
    assert linha.email == "ana@acme.com"
    assert linha.password_hash == HASH
    assert linha.role == "user"
    assert linha.created_at is not None


async def test_outra_violacao_nao_e_confundida_com_email_repetido(
    session: AsyncSession,
) -> None:
    repository = SqlUserRepository(session)
    primeiro = User.register(Email("ana@acme.com"), PasswordHash(HASH))
    await repository.add(primeiro)
    mesmo_id = User(
        id=primeiro.id,
        email=Email("bia@acme.com"),
        password_hash=primeiro.password_hash,
    )

    with pytest.raises(IntegrityError):
        await repository.add(mesmo_id)
