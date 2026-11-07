from dataclasses import dataclass
from typing import Self

from app.users.domain.entities.user import User


@dataclass(frozen=True, slots=True)
class UserProfile:
    id: str
    email: str
    role: str

    @classmethod
    def from_user(cls, user: User) -> Self:
        return cls(id=str(user.id.value), email=user.email.value, role=user.role.value)
