from collections.abc import Sequence
from datetime import datetime, timedelta

from sqlalchemy import delete, select, tuple_
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.users.application.ports.attempt_limiter import (
    AttemptRule,
    seconds_until_release,
    window_start,
)
from app.users.infrastructure.persistence.models.auth_attempt_model import (
    AuthAttemptModel,
)

RETENCAO = timedelta(hours=2)


class SqlAttemptLimiter:
    """Cada operação usa a sua própria sessão: a falha de login precisa ficar
    gravada mesmo que o caso de uso termine sem commit."""

    def __init__(self, session_factory: async_sessionmaker[AsyncSession]) -> None:
        self._session_factory = session_factory

    async def retry_after(
        self, rules: Sequence[AttemptRule], now: datetime
    ) -> int | None:
        esperas: list[int] = []
        async with self._session_factory() as session:
            for regra in rules:
                inicio = window_start(now, regra.window)
                feitas = await session.scalar(
                    select(AuthAttemptModel.count).where(
                        AuthAttemptModel.scope == regra.scope,
                        AuthAttemptModel.key_hash == regra.key_hash,
                        AuthAttemptModel.window_start == inicio,
                    )
                )
                if feitas is not None and feitas >= regra.limit:
                    esperas.append(seconds_until_release(now, regra.window))
        return max(esperas) if esperas else None

    async def record(self, rules: Sequence[AttemptRule], now: datetime) -> None:
        async with self._session_factory() as session:
            for regra in rules:
                inserir = insert(AuthAttemptModel).values(
                    scope=regra.scope,
                    key_hash=regra.key_hash,
                    window_start=window_start(now, regra.window),
                    count=1,
                )
                await session.execute(
                    inserir.on_conflict_do_update(
                        index_elements=["scope", "key_hash", "window_start"],
                        set_={"count": AuthAttemptModel.count + 1},
                    )
                )
            await session.execute(
                delete(AuthAttemptModel).where(
                    AuthAttemptModel.window_start < now - RETENCAO
                )
            )
            await session.commit()

    async def reset(self, rules: Sequence[AttemptRule]) -> None:
        if len(rules) == 0:
            return
        async with self._session_factory() as session:
            await session.execute(
                delete(AuthAttemptModel).where(
                    tuple_(AuthAttemptModel.scope, AuthAttemptModel.key_hash).in_(
                        [(r.scope, r.key_hash) for r in rules]
                    )
                )
            )
            await session.commit()
