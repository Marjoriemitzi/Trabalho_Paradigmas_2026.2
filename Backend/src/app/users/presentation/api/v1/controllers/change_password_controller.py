from collections.abc import Callable
from dataclasses import dataclass

from fastapi import Response

from app.users.application.ports.token_verifier import AuthenticatedUser
from app.users.application.use_cases.change_password import (
    ChangePasswordInputPort,
    ChangePasswordOutputPort,
)
from app.users.presentation.api.v1.presenters.change_password_presenter import (
    ChangePasswordHttpPresenter,
)
from app.users.presentation.api.v1.schemas.change_password import (
    ChangePasswordRequest,
)

ChangePasswordFactory = Callable[[ChangePasswordOutputPort], ChangePasswordInputPort]


@dataclass(frozen=True, slots=True)
class ChangePasswordController:
    build_interactor: ChangePasswordFactory

    async def handle(
        self, request: ChangePasswordRequest, current: AuthenticatedUser
    ) -> Response:
        presenter = ChangePasswordHttpPresenter()
        await self.build_interactor(presenter).execute(request.to_input(current.id))
        return presenter.response()
