from collections.abc import Sequence
from datetime import datetime

from app.users.application.ports.attempt_limiter import (
    AttemptRule,
    seconds_until_release,
    window_start,
)


class FakeAttemptLimiter:
    def __init__(self) -> None:
        self.counts: dict[tuple[str, str, datetime], int] = {}

    async def retry_after(
        self, rules: Sequence[AttemptRule], now: datetime
    ) -> int | None:
        esperas = [
            seconds_until_release(now, r.window)
            for r in rules
            if self.counts.get((r.scope, r.key_hash, window_start(now, r.window)), 0)
            >= r.limit
        ]
        return max(esperas) if esperas else None

    async def record(self, rules: Sequence[AttemptRule], now: datetime) -> None:
        for r in rules:
            chave = (r.scope, r.key_hash, window_start(now, r.window))
            self.counts[chave] = self.counts.get(chave, 0) + 1

    async def reset(self, rules: Sequence[AttemptRule]) -> None:
        alvo = {(r.scope, r.key_hash) for r in rules}
        self.counts = {k: v for k, v in self.counts.items() if k[:2] not in alvo}
