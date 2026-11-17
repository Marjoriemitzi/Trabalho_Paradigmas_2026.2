from fastapi.responses import JSONResponse

from app.users.application.use_cases.change_password import ChangePasswordInteractor
from app.users.application.use_cases.change_password import (
    ChangePasswordRequest as DtoRequest,
)
from app.users.presentation.api.v1.presenters.change_password_presenter import (
    ChangePasswordHttpPresenter,
)
from app.users.presentation.api.v1.schemas.change_password import ChangePasswordRequest


class ChangePasswordController:
    def __init__(
        self,
        interactor: ChangePasswordInteractor,
        presenter: ChangePasswordHttpPresenter,
    ) -> None:
        self._interactor = interactor
        self._presenter = presenter

    async def handle(self, body: ChangePasswordRequest, user_id: str) -> JSONResponse:
        dto = DtoRequest(
            user_id=user_id,
            current_password=body.current_password.get_secret_value(),
            new_password=body.new_password.get_secret_value(),
        )
        await self._interactor.execute(dto)
        return self._presenter.response()
