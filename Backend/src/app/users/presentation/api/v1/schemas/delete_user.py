from pydantic import BaseModel, ConfigDict, SecretStr


class DeleteUserRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    password: SecretStr
