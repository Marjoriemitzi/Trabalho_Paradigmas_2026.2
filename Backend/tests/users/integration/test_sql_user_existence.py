import uuid

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.users.domain.entities.user import User
from app.users.domain.value_objects.email import Email
from app.users.domain.value_objects.password import PasswordHash
from app.users.domain.value_objects.user_id import UserId
from app.users.infrastructure.persistence.repositories.sql_user_repository import (
    SqlUserRepository,
)
from app.users.infrastructure.persistence.user_existence import SqlUserExistence


async def test_diz_se_o_usuario_existe(
    session: AsyncSession, session_factory: async_sessionmaker[AsyncSession]
) -> None:
    user = User.register(Email("ana@acme.com"), PasswordHash("hash"))
    await SqlUserRepository(session).add(user)
    existencia = SqlUserExistence(session_factory)

    assert await existencia.exists(user.id) is True
    assert await existencia.exists(UserId(uuid.uuid4())) is False
