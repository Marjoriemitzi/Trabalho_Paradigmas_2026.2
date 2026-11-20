from collections.abc import Callable
from dataclasses import dataclass

from fastapi import Response

from app.users.application.use_cases.logout import (
    LogoutInputPort,
    LogoutOutputPort,
)
from app.users.presentation.api.v1.presenters.logout_presenter import (
    LogoutHttpPresenter,
)
from app.users.presentation.api.v1.schemas.refresh_session import (
    RefreshSessionRequest,
)

LogoutFactory = Callable[[LogoutOutputPort], LogoutInputPort]


@dataclass(frozen=True, slots=True)
class LogoutController:
    build_interactor: LogoutFactory

    async def handle(self, request: RefreshSessionRequest) -> Response:
        presenter = LogoutHttpPresenter()
        await self.build_interactor(presenter).execute(request.to_logout_input())
        return presenter.response()
