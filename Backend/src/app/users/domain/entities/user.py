from dataclasses import dataclass
from typing import Self, override

from app.users.domain.value_objects.email import Email
from app.users.domain.value_objects.password import PasswordHash
from app.users.domain.value_objects.role import Role
from app.users.domain.value_objects.user_id import UserId


@dataclass(eq=False, slots=True)
class User:
    id: UserId
    email: Email
    password_hash: PasswordHash
    role: Role = Role.USER

    @classmethod
    def register(cls, email: Email, password_hash: PasswordHash) -> Self:
        return cls(id=UserId.new(), email=email, password_hash=password_hash)

    def change_password(self, new_hash: PasswordHash) -> None:
        self.password_hash = new_hash

    @override
    def __eq__(self, other: object) -> bool:
        return isinstance(other, User) and other.id == self.id

    @override
    def __hash__(self) -> int:
        return hash(self.id)
