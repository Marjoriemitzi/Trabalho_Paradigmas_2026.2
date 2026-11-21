from typing import Self

from pydantic import BaseModel

from app.shared.presentation.api.schema_types import UuidStr
from app.users.application.dtos.get_current_user import UserProfile


class UserProfileResponse(BaseModel):
    id: UuidStr
    email: str
    role: str

    @classmethod
    def from_profile(cls, user: UserProfile) -> Self:
        return cls(id=user.id, email=user.email, role=user.role)
