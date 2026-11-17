from dataclasses import dataclass
from datetime import datetime
from typing import Protocol


class LogoutUserOutputPort(Protocol):
    def present_success(self) -> None: ...


@dataclass(frozen=True)
class LogoutUserRequest:
    jti: str
    user_id: str
    expires_at: datetime


class LogoutUserInputPort(Protocol):
    async def execute(self, request: LogoutUserRequest) -> None: ...
