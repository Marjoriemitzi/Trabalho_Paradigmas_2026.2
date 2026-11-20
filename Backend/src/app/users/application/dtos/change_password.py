from dataclasses import dataclass, field

from app.users.domain.value_objects.user_id import UserId


@dataclass(frozen=True, slots=True)
class ChangePasswordInput:
    user_id: UserId
    current_password: str = field(repr=False)
    new_password: str = field(repr=False)
