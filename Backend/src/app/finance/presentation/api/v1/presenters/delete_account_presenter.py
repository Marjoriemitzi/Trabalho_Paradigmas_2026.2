from fastapi import status
from fastapi.responses import JSONResponse

from app.finance.application.use_cases.delete_account import DeleteAccountOutputPort
from app.shared.presentation.api.errors import error_response


class DeleteAccountHttpPresenter(DeleteAccountOutputPort):
    def __init__(self) -> None:
        self._response: JSONResponse | None = None

    def response(self) -> JSONResponse:
        if self._response is None:
            raise RuntimeError("Erro")
        return self._response

    def present_success(self) -> None:
        self._response = JSONResponse(None, status_code=status.HTTP_204_NO_CONTENT)

    def present_account_not_found(self) -> None:
        self._response = error_response(status.HTTP_404_NOT_FOUND, "account_not_found")

    def present_account_in_use(self) -> None:
        self._response = error_response(status.HTTP_409_CONFLICT, "account_in_use")
