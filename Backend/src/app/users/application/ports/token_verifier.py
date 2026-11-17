from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Protocol

from app.users.domain.entities.user import UserId


@dataclass(frozen=True)
class AuthenticatedUser:
    id: UserId
    role: str
    jti: str = ""
    exp: datetime = field(default_factory=lambda: datetime.now(UTC))


class TokenVerifier(Protocol):
    def verify(self, token: str) -> AuthenticatedUser | None: ...
