from dataclasses import dataclass
from typing import Protocol

from app.users.domain.entities.user import User


@dataclass(frozen=True)
class AccessToken:
    value: str
    expires_in: int


class TokenIssuer(Protocol):
    def issue(self, user: User) -> AccessToken: ...
