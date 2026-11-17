from fastapi import status
from fastapi.responses import JSONResponse

from app.shared.presentation.api.errors import error_response
from app.users.application.use_cases.change_password import ChangePasswordOutputPort


class ChangePasswordHttpPresenter(ChangePasswordOutputPort):
    def __init__(self) -> None:
        self._response: JSONResponse | None = None

    def response(self) -> JSONResponse:
        if self._response is None:
            raise RuntimeError("Nenhum resultado.")
        return self._response

    def present_success(self) -> None:
        self._response = JSONResponse(None, status_code=status.HTTP_204_NO_CONTENT)

    def present_invalid_current_password(self) -> None:
        self._response = error_response(
            status.HTTP_422_UNPROCESSABLE_CONTENT, "invalid_current_password"
        )

    def present_weak_password(self, reasons: list[str]) -> None:
        self._response = error_response(
            status.HTTP_422_UNPROCESSABLE_CONTENT, "weak_password", reasons=reasons
        )

    def present_user_not_found(self) -> None:
        self._response = error_response(status.HTTP_401_UNAUTHORIZED, "invalid_token")
