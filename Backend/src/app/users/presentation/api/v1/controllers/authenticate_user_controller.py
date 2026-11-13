from collections.abc import Callable
from dataclasses import dataclass

from fastapi.responses import JSONResponse

from app.users.application.use_cases.authenticate_user import (
    AuthenticateUserInputPort,
    AuthenticateUserOutputPort,
)
from app.users.presentation.api.v1.presenters.authenticate_user_presenter import (
    AuthenticateUserHttpPresenter,
)
from app.users.presentation.api.v1.schemas.authenticate_user import (
    AuthenticateUserRequest,
)

AuthenticateUserFactory = Callable[
    [AuthenticateUserOutputPort], AuthenticateUserInputPort
]


@dataclass(frozen=True, slots=True)
class AuthenticateUserController:
    build_interactor: AuthenticateUserFactory

    async def handle(self, request: AuthenticateUserRequest) -> JSONResponse:
        presenter = AuthenticateUserHttpPresenter()
        await self.build_interactor(presenter).execute(request.to_input())
        return presenter.response()
