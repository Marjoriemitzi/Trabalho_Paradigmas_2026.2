from collections.abc import Callable
from dataclasses import dataclass

from fastapi import Response

from app.users.application.ports.token_verifier import AuthenticatedUser
from app.users.application.use_cases.delete_user import (
    DeleteUserInputPort,
    DeleteUserOutputPort,
)
from app.users.presentation.api.v1.presenters.delete_user_presenter import (
    DeleteUserHttpPresenter,
)
from app.users.presentation.api.v1.schemas.delete_user import DeleteUserRequest

DeleteUserFactory = Callable[[DeleteUserOutputPort], DeleteUserInputPort]


@dataclass(frozen=True, slots=True)
class DeleteUserController:
    build_interactor: DeleteUserFactory

    async def handle(
        self, request: DeleteUserRequest, current: AuthenticatedUser
    ) -> Response:
        presenter = DeleteUserHttpPresenter()
        await self.build_interactor(presenter).execute(request.to_input(current.id))
        return presenter.response()
