import math
from collections.abc import Sequence
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from typing import Literal, Protocol

AttemptScope = Literal["login_pair", "login_ip", "register_ip"]


@dataclass(frozen=True, slots=True)
class AttemptRule:
    scope: AttemptScope
    key_hash: str
    limit: int
    window: timedelta


def window_start(now: datetime, window: timedelta) -> datetime:
    segundos = int(window.total_seconds())
    inicio = int(now.timestamp()) // segundos * segundos
    return datetime.fromtimestamp(inicio, tz=UTC)


def seconds_until_release(now: datetime, window: timedelta) -> int:
    fim = window_start(now, window) + window
    return max(1, math.ceil((fim - now).total_seconds()))


class AttemptLimiter(Protocol):
    async def retry_after(
        self, rules: Sequence[AttemptRule], now: datetime
    ) -> int | None:
        """Segundos até liberar, se alguma regra já estourou; None se nenhuma."""
        ...

    async def record(self, rules: Sequence[AttemptRule], now: datetime) -> None: ...

    async def reset(self, rules: Sequence[AttemptRule]) -> None: ...
