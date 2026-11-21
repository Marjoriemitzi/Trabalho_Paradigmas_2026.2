import uuid
from datetime import timedelta

import pytest
from sqlalchemy import delete
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.users.application.ports.attempt_limiter import AttemptLimiter
from app.users.infrastructure.persistence.models.auth_attempt_model import (
    AuthAttemptModel,
)
from app.users.infrastructure.persistence.sql_attempt_limiter import SqlAttemptLimiter
from tests.users.contracts.attempt_limiter_contract import (
    AGORA,
    AttemptLimiterContract,
    regra,
)


class TestSqlAttemptLimiter(AttemptLimiterContract):
    @pytest.fixture
    async def limiter(
        self, session_factory: async_sessionmaker[AsyncSession], connection: object
    ) -> AttemptLimiter:
        return SqlAttemptLimiter(session_factory)


async def test_a_gravacao_apaga_as_janelas_com_mais_de_duas_horas(
    session_factory: async_sessionmaker[AsyncSession],
) -> None:
    limiter = SqlAttemptLimiter(session_factory)
    velha, nova = regra(uuid.uuid4().hex * 2), regra(uuid.uuid4().hex * 2)
    await limiter.record([velha], AGORA - timedelta(hours=3))

    await limiter.record([nova], AGORA)

    assert await limiter.retry_after([velha], AGORA - timedelta(hours=3)) is None
    async with session_factory() as session:
        await session.execute(
            delete(AuthAttemptModel).where(AuthAttemptModel.key_hash == nova.key_hash)
        )
        await session.commit()
