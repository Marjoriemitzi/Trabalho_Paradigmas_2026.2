from typing import Self

from pydantic import BaseModel, ConfigDict, SecretStr

from app.shared.presentation.api.schema_types import UuidStr
from app.users.application.dtos.register_user import RegisteredUser, RegisterUserInput


class RegisterUserRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    email: str
    password: SecretStr

    def to_input(self, client_ip: str) -> RegisterUserInput:
        return RegisterUserInput(
            email=self.email,
            password=self.password.get_secret_value(),
            client_ip=client_ip,
        )


class RegisteredUserResponse(BaseModel):
    id: UuidStr
    email: str
    role: str

    @classmethod
    def from_output(cls, user: RegisteredUser) -> Self:
        return cls(id=user.id, email=user.email, role=user.role)
