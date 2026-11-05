"""
Dados que entram e saem do caso de uso de cadastro.
"""

from dataclasses import dataclass, field
from typing import Self

from app.users.domain.entities.user import User


@dataclass(frozen=True, slots=True)
class RegisterUserInput:
    email: str
    password: str = field(repr=False)


@dataclass(frozen=True, slots=True)
class RegisteredUser:
    id: str
    email: str
    role: str

    @classmethod
    def from_user(cls, user: User) -> Self:
        return cls(id=str(user.id.value), email=user.email.value, role=user.role.value)
