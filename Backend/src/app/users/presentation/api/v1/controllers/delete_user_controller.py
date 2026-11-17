from fastapi.responses import JSONResponse

from app.users.application.use_cases.delete_user import DeleteUserInteractor
from app.users.application.use_cases.delete_user import DeleteUserRequest as DtoRequest
from app.users.presentation.api.v1.presenters.delete_user_presenter import (
    DeleteUserHttpPresenter,
)
from app.users.presentation.api.v1.schemas.delete_user import DeleteUserRequest


class DeleteUserController:
    def __init__(
        self, interactor: DeleteUserInteractor, presenter: DeleteUserHttpPresenter
    ) -> None:
        self._interactor = interactor
        self._presenter = presenter

    async def handle(self, body: DeleteUserRequest, user_id: str) -> JSONResponse:
        await self._interactor.execute(
            DtoRequest(user_id=user_id, password=body.password.get_secret_value())
        )
        return self._presenter.response()
