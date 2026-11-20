import uuid
from dataclasses import dataclass
from datetime import datetime
from typing import Protocol

from app.users.domain.value_objects.role import Role
from app.users.domain.value_objects.user_id import UserId


@dataclass(frozen=True, slots=True)
class AuthenticatedUser:
    id: UserId
    role: Role
    jti: uuid.UUID
    expires_at: datetime


class TokenVerifier(Protocol):
    def verify(self, token: str) -> AuthenticatedUser | None: ...
