from collections.abc import Callable
from dataclasses import dataclass

from fastapi.responses import JSONResponse

from app.users.application.use_cases.refresh_session import (
    RefreshSessionInputPort,
    RefreshSessionOutputPort,
)
from app.users.presentation.api.v1.presenters.refresh_session_presenter import (
    RefreshSessionHttpPresenter,
)
from app.users.presentation.api.v1.schemas.refresh_session import (
    RefreshSessionRequest,
)

RefreshSessionFactory = Callable[[RefreshSessionOutputPort], RefreshSessionInputPort]


@dataclass(frozen=True, slots=True)
class RefreshSessionController:
    build_interactor: RefreshSessionFactory

    async def handle(self, request: RefreshSessionRequest) -> JSONResponse:
        presenter = RefreshSessionHttpPresenter()
        await self.build_interactor(presenter).execute(request.to_refresh_input())
        return presenter.response()
