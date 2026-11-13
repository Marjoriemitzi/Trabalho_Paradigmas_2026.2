from collections.abc import Callable
from dataclasses import dataclass

from fastapi.responses import JSONResponse

from app.users.application.use_cases.register_user import (
    RegisterUserInputPort,
    RegisterUserOutputPort,
)
from app.users.presentation.api.v1.presenters.register_user_presenter import (
    RegisterUserHttpPresenter,
)
from app.users.presentation.api.v1.schemas.register_user import RegisterUserRequest

RegisterUserFactory = Callable[[RegisterUserOutputPort], RegisterUserInputPort]


@dataclass(frozen=True, slots=True)
class RegisterUserController:
    build_interactor: RegisterUserFactory

    async def handle(self, request: RegisterUserRequest) -> JSONResponse:
        presenter = RegisterUserHttpPresenter()
        await self.build_interactor(presenter).execute(request.to_input())
        return presenter.response()
