import uuid
from collections.abc import Awaitable, Callable

import pytest
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncConnection, AsyncSession

from app.users.domain.repositories.refresh_token_repository import (
    RefreshTokenRepository,
)
from app.users.domain.value_objects.user_id import UserId
from app.users.infrastructure.persistence.repositories.sql_refresh_token_repository import (  # noqa: E501
    SqlRefreshTokenRepository,
)
from tests.users.contracts.refresh_token_repository_contract import (
    RefreshTokenRepositoryContract,
)


@pytest.fixture
def novo_usuario(connection: AsyncConnection) -> Callable[[], Awaitable[UserId]]:
    async def criar() -> UserId:
        user_id = uuid.uuid4()
        await connection.execute(
            text(
                "INSERT INTO users (id, email, password_hash, role)"
                " VALUES (:id, :email, 'hash', 'user')"
            ),
            {"id": user_id, "email": f"{user_id.hex}@acme.com"},
        )
        return UserId(user_id)

    return criar


class TestSqlRefreshTokenRepository(RefreshTokenRepositoryContract):
    @pytest.fixture
    def repository(self, session: AsyncSession) -> RefreshTokenRepository:
        return SqlRefreshTokenRepository(session)

    @pytest.fixture
    async def usuario(self, novo_usuario: Callable[[], Awaitable[UserId]]) -> UserId:
        return await novo_usuario()

    @pytest.fixture
    async def outro_usuario(
        self, novo_usuario: Callable[[], Awaitable[UserId]]
    ) -> UserId:
        return await novo_usuario()
