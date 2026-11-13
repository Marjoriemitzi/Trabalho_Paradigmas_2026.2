from fastapi import status
from fastapi.responses import JSONResponse

from app.finance.application.dtos.get_statement import StatementOutput
from app.finance.application.use_cases.get_statement import GetStatementOutputPort
from app.finance.presentation.api.v1.schemas.get_statement import StatementResponse
from app.shared.presentation.api.errors import error_response


class GetStatementHttpPresenter(GetStatementOutputPort):
    def __init__(self) -> None:
        self._response: JSONResponse | None = None

    def response(self) -> JSONResponse:
        if self._response is None:
            raise RuntimeError("O caso de uso terminou sem apresentar um resultado.")
        return self._response

    def present_statement(self, statement: StatementOutput) -> None:
        corpo = StatementResponse.from_output(statement).model_dump(by_alias=True)
        self._response = JSONResponse(
            corpo,
            status_code=status.HTTP_200_OK,
            headers={"Cache-Control": "no-store"},
        )

    def present_invalid(self, field: str, problem: str) -> None:
        self._response = error_response(
            status.HTTP_422_UNPROCESSABLE_CONTENT,
            "invalid_period",
            fields=[{"field": field, "problem": problem}],
        )

    def present_account_not_found(self) -> None:
        self._response = error_response(status.HTTP_404_NOT_FOUND, "account_not_found")
