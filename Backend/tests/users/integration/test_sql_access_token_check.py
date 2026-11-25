import uuid
from datetime import UTC, datetime, timedelta

import pytest
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.users.application.ports.access_token_check import AccessTokenCheck
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
from tests.users.contracts.access_token_check_contract import (
    AccessTokenCheckContract,
    Bloquear,
)


class TestSqlAccessTokenCheck(AccessTokenCheckContract):
    @pytest.fixture
    def check(
        self, session_factory: async_sessionmaker[AsyncSession]
    ) -> AccessTokenCheck:
        return SqlAccessTokenCheck(session_factory)

    @pytest.fixture
    async def usuario(self, session: AsyncSession) -> UserId:
        user = User.register(Email("ana@acme.com"), PasswordHash("hash"))
        await SqlUserRepository(session).add(user)
        return user.id

    @pytest.fixture
    def bloquear(self, session: AsyncSession) -> Bloquear:
        async def _bloquear(jti: uuid.UUID, usuario: UserId) -> None:
            await SqlTokenBlocklist(session).add(
                jti, usuario, datetime.now(UTC) + timedelta(minutes=15)
            )

        return _bloquear
