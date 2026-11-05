"""
Entidade User:
    Um usuário cadastrado, com identidade própria.
"""

from dataclasses import dataclass
from typing import Self

from app.users.domain.value_objects.email import Email
from app.users.domain.value_objects.password import PasswordHash
from app.users.domain.value_objects.role import Role
from app.users.domain.value_objects.user_id import UserId


@dataclass(slots=True)
class User:
    id: UserId
    email: Email
    password_hash: PasswordHash
    role: Role = Role.USER

    @classmethod
    def register(cls, email: Email, password_hash: PasswordHash) -> Self:
        """Cadastra um usuário novo, com uma identidade nova."""
        return cls(id=UserId.new(), email=email, password_hash=password_hash)

    def __eq__(self, other: object) -> bool:
        return isinstance(other, User) and other.id == self.id

    def __hash__(self) -> int:
        return hash(self.id)
