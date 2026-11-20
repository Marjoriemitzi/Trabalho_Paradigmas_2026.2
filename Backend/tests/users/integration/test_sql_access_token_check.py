import uuid
from datetime import UTC, datetime, timedelta

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.users.domain.entities.user import User
from app.users.domain.value_objects.email import Email
from app.users.domain.value_objects.password import PasswordHash
from app.users.domain.value_objects.user_id import UserId
from app.users.infrastructure.persistence.access_token_check import SqlAccessTokenCheck
from app.users.infrastructure.persistence.repositories.sql_token_blocklist import (
    SqlTokenBlocklist,
)
from app.users.infrastructure.persistence.repositories.sql_user_repository import (
    SqlUserRepository,
)
from tests.users.fakes.authenticated import autenticado


async def test_so_vale_o_token_de_usuario_que_existe(
    session: AsyncSession, session_factory: async_sessionmaker[AsyncSession]
) -> None:
    user = User.register(Email("ana@acme.com"), PasswordHash("hash"))
    await SqlUserRepository(session).add(user)
    check = SqlAccessTokenCheck(session_factory)

    assert await check.is_valid(autenticado(user.id)) is True
    assert await check.is_valid(autenticado(UserId(uuid.uuid4()))) is False


async def test_token_na_blocklist_nao_vale_mais(
    session: AsyncSession, session_factory: async_sessionmaker[AsyncSession]
) -> None:
    user = User.register(Email("ana@acme.com"), PasswordHash("hash"))
    await SqlUserRepository(session).add(user)
    revogado, outro = autenticado(user.id), autenticado(user.id)
    await SqlTokenBlocklist(session).add(
        revogado.jti, user.id, datetime.now(UTC) + timedelta(minutes=15)
    )
    check = SqlAccessTokenCheck(session_factory)

    assert await check.is_valid(revogado) is False
    assert await check.is_valid(outro) is True
