from pydantic import BaseModel, ConfigDict, Field, SecretStr

from app.users.application.dtos.change_password import ChangePasswordInput
from app.users.domain.value_objects.user_id import UserId


class ChangePasswordRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    current_password: SecretStr = Field(min_length=1)
    new_password: SecretStr

    def to_input(self, user_id: UserId) -> ChangePasswordInput:
        return ChangePasswordInput(
            user_id=user_id,
            current_password=self.current_password.get_secret_value(),
            new_password=self.new_password.get_secret_value(),
        )
