from typing import Self

from pydantic import BaseModel

from app.users.application.dtos.get_current_user import UserProfile


class UserProfileResponse(BaseModel):
    id: str
    email: str
    role: str

    @classmethod
    def from_profile(cls, user: UserProfile) -> Self:
        return cls(id=user.id, email=user.email, role=user.role)
