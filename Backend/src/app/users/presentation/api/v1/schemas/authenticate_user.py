from typing import Literal, Self

from pydantic import BaseModel, ConfigDict, SecretStr

from app.users.application.dtos.authenticate_user import AuthenticateUserInput
from app.users.application.ports.token_issuer import AccessToken


class AuthenticateUserRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    email: str
    password: SecretStr

    def to_input(self) -> AuthenticateUserInput:
        return AuthenticateUserInput(
            email=self.email, password=self.password.get_secret_value()
        )


class AccessTokenResponse(BaseModel):
    access_token: str
    token_type: Literal["bearer"] = "bearer"
    expires_in: int

    @classmethod
    def from_token(cls, token: AccessToken) -> Self:
        return cls(access_token=token.value, expires_in=token.expires_in)
