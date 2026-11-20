from typing import override

from fastapi import Response, status

from app.finance.application.use_cases.delete_account import DeleteAccountOutputPort
from app.shared.presentation.api.errors import error_response


class DeleteAccountHttpPresenter(DeleteAccountOutputPort):
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
    def present_in_use(self) -> None:
        self._response = error_response(status.HTTP_409_CONFLICT, "account_in_use")

    @override
    def present_not_found(self) -> None:
        self._response = error_response(status.HTTP_404_NOT_FOUND, "account_not_found")
