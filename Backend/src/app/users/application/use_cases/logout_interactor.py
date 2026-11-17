from datetime import UTC, datetime
from typing import Any

from app.users.application.use_cases.logout_user import (
    LogoutUserInputPort,
    LogoutUserOutputPort,
    LogoutUserRequest,
)


class LogoutInteractor(LogoutUserInputPort):
    def __init__(self, uow: Any, presenter: LogoutUserOutputPort) -> None:
        self._uow = uow
        self._presenter = presenter

    async def execute(self, request: LogoutUserRequest) -> None:
        await self._uow.token_blocklist.add(
            jti=request.jti,
            user_id=request.user_id,
            expires_at=request.expires_at,
        )
        await self._uow.token_blocklist.delete_expired(datetime.now(UTC))
        await self._uow.commit()
        self._presenter.present_success()
