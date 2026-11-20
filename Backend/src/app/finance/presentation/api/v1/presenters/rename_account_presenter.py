from fastapi import status
from fastapi.responses import JSONResponse

from app.finance.application.dtos.create_account import AccountOutput
from app.finance.application.use_cases.rename_account import RenameAccountOutputPort
from app.finance.presentation.api.v1.schemas.accounts import AccountResponse
from app.shared.presentation.api.errors import error_response


class RenameAccountHttpPresenter(RenameAccountOutputPort):
    def __init__(self) -> None:
        self._response: JSONResponse | None = None

    def response(self) -> JSONResponse:
        if self._response is None:
            raise RuntimeError("O caso de uso terminou sem apresentar um resultado.")
        return self._response

    def present_renamed(self, account: AccountOutput) -> None:
        corpo = AccountResponse.from_output(account).model_dump()
        self._response = JSONResponse(corpo, status_code=status.HTTP_200_OK)

    def present_invalid(self, field: str, problem: str) -> None:
        self._response = error_response(
            status.HTTP_422_UNPROCESSABLE_CONTENT,
            "invalid_account",
            fields=[{"field": field, "problem": problem}],
        )

    def present_name_taken(self, name: str) -> None:
        self._response = error_response(status.HTTP_409_CONFLICT, "account_name_taken")

    def present_not_found(self) -> None:
        self._response = error_response(status.HTTP_404_NOT_FOUND, "account_not_found")
