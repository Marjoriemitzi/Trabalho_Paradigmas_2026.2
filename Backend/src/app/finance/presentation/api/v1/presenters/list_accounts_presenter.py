from fastapi import status
from fastapi.responses import JSONResponse

from app.finance.application.dtos.list_accounts import AccountSummary
from app.finance.application.use_cases.list_accounts import ListAccountsOutputPort
from app.finance.presentation.api.v1.schemas.accounts import (
    AccountListResponse,
    AccountSummaryResponse,
)


class ListAccountsHttpPresenter(ListAccountsOutputPort):
    def __init__(self) -> None:
        self._response: JSONResponse | None = None

    def response(self) -> JSONResponse:
        if self._response is None:
            raise RuntimeError("O caso de uso terminou sem apresentar um resultado.")
        return self._response

    def present_accounts(self, accounts: tuple[AccountSummary, ...]) -> None:
        corpo = AccountListResponse(
            accounts=[AccountSummaryResponse.from_summary(a) for a in accounts]
        ).model_dump()
        self._response = JSONResponse(
            corpo,
            status_code=status.HTTP_200_OK,
            headers={"Cache-Control": "no-store"},
        )
