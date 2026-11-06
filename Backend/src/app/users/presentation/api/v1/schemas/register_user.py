from typing import Self

from pydantic import BaseModel, ConfigDict, SecretStr

from app.users.application.dtos.register_user import RegisteredUser, RegisterUserInput


class RegisterUserRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    email: str
    password: SecretStr

    def to_input(self) -> RegisterUserInput:
        return RegisterUserInput(
            email=self.email, password=self.password.get_secret_value()
        )


class RegisteredUserResponse(BaseModel):
    id: str
    email: str
    role: str

    @classmethod
    def from_output(cls, user: RegisteredUser) -> Self:
        return cls(id=user.id, email=user.email, role=user.role)
