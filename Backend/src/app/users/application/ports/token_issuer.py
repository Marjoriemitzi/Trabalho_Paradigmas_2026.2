from dataclasses import dataclass, field
from typing import Protocol

from app.users.domain.entities.user import User


@dataclass(frozen=True, slots=True)
class AccessToken:
    value: str = field(repr=False)
    expires_in: int


class TokenIssuer(Protocol):
    def issue(self, user: User) -> AccessToken: ...
