from pydantic import BaseModel, ConfigDict, Field, SecretStr

from app.users.application.dtos.delete_user import DeleteUserInput
from app.users.domain.value_objects.user_id import UserId


class DeleteUserRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    password: SecretStr = Field(min_length=1)

    def to_input(self, user_id: UserId) -> DeleteUserInput:
        return DeleteUserInput(
            user_id=user_id, password=self.password.get_secret_value()
        )
