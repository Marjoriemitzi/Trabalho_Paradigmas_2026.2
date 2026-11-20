from pydantic import BaseModel, ConfigDict, Field, SecretStr

from app.users.application.dtos.refresh_session import LogoutInput, RefreshSessionInput
from app.users.application.ports.token_verifier import AuthenticatedUser


class RefreshSessionRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    refresh_token: SecretStr = Field(min_length=1)

    def to_refresh_input(self) -> RefreshSessionInput:
        return RefreshSessionInput(refresh_token=self.refresh_token.get_secret_value())

    def to_logout_input(self, current: AuthenticatedUser | None = None) -> LogoutInput:
        return LogoutInput(
            refresh_token=self.refresh_token.get_secret_value(), current=current
        )
