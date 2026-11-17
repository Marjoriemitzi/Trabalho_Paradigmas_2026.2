from fastapi import status
from fastapi.responses import JSONResponse

from app.finance.application.dtos.record_transaction import RecordedTransaction
from app.finance.application.use_cases.record_transaction import (
    RecordTransactionOutputPort,
)
from app.finance.presentation.api.v1.schemas.record_transaction import (
    RecordedTransactionResponse,
)
from app.shared.presentation.api.errors import error_response


class RecordTransactionHttpPresenter(RecordTransactionOutputPort):
    def __init__(self) -> None:
        self._response: JSONResponse | None = None

    def response(self) -> JSONResponse:
        if self._response is None:
            raise RuntimeError("O caso de uso terminou sem apresentar um resultado.")
        return self._response

    def present_recorded(self, transaction: RecordedTransaction) -> None:
        corpo = RecordedTransactionResponse.from_output(transaction).model_dump()
        self._response = JSONResponse(corpo, status_code=status.HTTP_201_CREATED)

    def present_invalid(self, field: str, problem: str) -> None:
        self._response = error_response(
            status.HTTP_422_UNPROCESSABLE_CONTENT,
            "invalid_transaction",
            fields=[{"field": field, "problem": problem}],
        )
