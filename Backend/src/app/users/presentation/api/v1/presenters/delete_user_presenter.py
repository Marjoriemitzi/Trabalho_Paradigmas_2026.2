from typing import override

from fastapi import Response, status

from app.shared.presentation.api.errors import error_response
from app.users.application.use_cases.delete_user import DeleteUserOutputPort
from app.users.presentation.api.v1.security import invalid_token


class DeleteUserHttpPresenter(DeleteUserOutputPort):
    def __init__(self) -> None:
        self._response: Response | None = None

    def response(self) -> Response:
        if self._response is None:
            raise RuntimeError("O caso de uso terminou sem apresentar um resultado.")
        return self._response

    @override
    def present_deleted(self) -> None:
        self._response = Response(status_code=status.HTTP_204_NO_CONTENT)

    @override
    def present_invalid_current_password(self) -> None:
        self._response = error_response(
            status.HTTP_422_UNPROCESSABLE_CONTENT, "invalid_current_password"
        )

    @override
    def present_user_not_found(self) -> None:
        raise invalid_token()
