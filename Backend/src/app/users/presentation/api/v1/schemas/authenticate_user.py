from typing import Literal, Self

from pydantic import BaseModel, ConfigDict, SecretStr

from app.users.application.dtos.authenticate_user import AuthenticateUserInput
from app.users.application.session import Session


class AuthenticateUserRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    email: str
    password: SecretStr

    def to_input(self, client_ip: str) -> AuthenticateUserInput:
        return AuthenticateUserInput(
            email=self.email,
            password=self.password.get_secret_value(),
            client_ip=client_ip,
        )


class SessionResponse(BaseModel):
    access_token: str
    token_type: Literal["bearer"] = "bearer"
    expires_in: int
    refresh_token: str
    refresh_expires_in: int

    @classmethod
    def from_session(cls, session: Session) -> Self:
        return cls(
            access_token=session.access_token.value,
            expires_in=session.access_token.expires_in,
            refresh_token=session.refresh_token,
            refresh_expires_in=session.refresh_expires_in,
        )
