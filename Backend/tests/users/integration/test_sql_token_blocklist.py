import uuid

import pytest
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncConnection, AsyncSession

from app.users.application.ports.token_blocklist import TokenBlocklist
from app.users.domain.value_objects.user_id import UserId
from app.users.infrastructure.persistence.repositories.sql_token_blocklist import (
    SqlTokenBlocklist,
)
from tests.users.contracts.token_blocklist_contract import TokenBlocklistContract


class TestSqlTokenBlocklist(TokenBlocklistContract):
    @pytest.fixture
    def blocklist(self, session: AsyncSession) -> TokenBlocklist:
        return SqlTokenBlocklist(session)

    @pytest.fixture
    async def usuario(self, connection: AsyncConnection) -> UserId:
        user_id = uuid.uuid4()
        await connection.execute(
            text(
                "INSERT INTO users (id, email, password_hash, role)"
                " VALUES (:id, :email, 'hash', 'user')"
            ),
            {"id": user_id, "email": f"{user_id.hex}@acme.com"},
        )
        return UserId(user_id)
