from dataclasses import dataclass, field

from app.users.domain.value_objects.user_id import UserId


@dataclass(frozen=True, slots=True)
class DeleteUserInput:
    user_id: UserId
    password: str = field(repr=False)
