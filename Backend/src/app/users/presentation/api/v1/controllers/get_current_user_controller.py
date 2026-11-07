from collections.abc import Callable
from dataclasses import dataclass

from fastapi.responses import JSONResponse

from app.users.application.ports.token_verifier import AuthenticatedUser
from app.users.application.use_cases.get_current_user import (
    GetCurrentUserInputPort,
    GetCurrentUserOutputPort,
)
from app.users.presentation.api.v1.presenters.get_current_user_presenter import (
    GetCurrentUserHttpPresenter,
)

GetCurrentUserFactory = Callable[[GetCurrentUserOutputPort], GetCurrentUserInputPort]


@dataclass(frozen=True, slots=True)
class GetCurrentUserController:
    build_interactor: GetCurrentUserFactory

    async def handle(self, current: AuthenticatedUser) -> JSONResponse:
        presenter = GetCurrentUserHttpPresenter()
        await self.build_interactor(presenter).execute(current)
        return presenter.response()
