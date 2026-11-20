import hashlib
from collections.abc import Sequence
from dataclasses import dataclass
from datetime import timedelta

from app.users.application.ports.attempt_limiter import AttemptLimiter, AttemptRule
from app.users.application.ports.clock import Clock


@dataclass(frozen=True, slots=True)
class AttemptLimits:
    login_pair_max_failures: int = 5
    login_ip_max_failures: int = 50
    login_window: timedelta = timedelta(minutes=15)
    register_ip_max: int = 5
    register_window: timedelta = timedelta(hours=1)


def _hash(chave: str) -> str:
    return hashlib.sha256(chave.encode()).hexdigest()


@dataclass(frozen=True, slots=True)
class AttemptGuard:
    limiter: AttemptLimiter
    clock: Clock
    limits: AttemptLimits

    def login_rules(self, ip: str, email: str) -> tuple[AttemptRule, AttemptRule]:
        par = AttemptRule(
            "login_pair",
            _hash(f"{ip}|{email.strip().lower()}"),
            self.limits.login_pair_max_failures,
            self.limits.login_window,
        )
        so_ip = AttemptRule(
            "login_ip",
            _hash(ip),
            self.limits.login_ip_max_failures,
            self.limits.login_window,
        )
        return par, so_ip

    def register_rules(self, ip: str) -> tuple[AttemptRule]:
        return (
            AttemptRule(
                "register_ip",
                _hash(ip),
                self.limits.register_ip_max,
                self.limits.register_window,
            ),
        )

    async def retry_after(self, rules: Sequence[AttemptRule]) -> int | None:
        return await self.limiter.retry_after(rules, self.clock.now())

    async def record(self, rules: Sequence[AttemptRule]) -> None:
        await self.limiter.record(rules, self.clock.now())

    async def reset(self, rules: Sequence[AttemptRule]) -> None:
        await self.limiter.reset(rules)
