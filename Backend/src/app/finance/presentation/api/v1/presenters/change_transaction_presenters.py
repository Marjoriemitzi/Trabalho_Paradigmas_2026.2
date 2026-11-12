from fastapi import Response, status
from fastapi.responses import JSONResponse

from app.finance.application.dtos.record_transaction import RecordedTransaction
from app.finance.application.use_cases.delete_transaction import (
    DeleteTransactionOutputPort,
)
from app.finance.application.use_cases.update_transaction import (
    UpdateTransactionOutputPort,
)
from app.finance.presentation.api.v1.schemas.record_transaction import (
    RecordedTransactionResponse,
)
from app.shared.presentation.api.errors import error_response


def _not_found() -> JSONResponse:
    return error_response(status.HTTP_404_NOT_FOUND, "transaction_not_found")


class UpdateTransactionHttpPresenter(UpdateTransactionOutputPort):
    def __init__(self) -> None:
        self._response: JSONResponse | None = None

    def response(self) -> JSONResponse:
        if self._response is None:
            raise RuntimeError("O caso de uso terminou sem apresentar um resultado.")
        return self._response

    def present_updated(self, transaction: RecordedTransaction) -> None:
        corpo = RecordedTransactionResponse.from_output(transaction).model_dump()
        self._response = JSONResponse(corpo, status_code=status.HTTP_200_OK)

    def present_invalid(self, field: str, problem: str) -> None:
        self._response = error_response(
            status.HTTP_422_UNPROCESSABLE_CONTENT,
            "invalid_transaction",
            fields=[{"field": field, "problem": problem}],
        )

    def present_not_found(self) -> None:
        self._response = _not_found()


class DeleteTransactionHttpPresenter(DeleteTransactionOutputPort):
    def __init__(self) -> None:
        self._response: Response | None = None

    def response(self) -> Response:
        if self._response is None:
            raise RuntimeError("O caso de uso terminou sem apresentar um resultado.")
        return self._response

    def present_deleted(self) -> None:
        self._response = Response(status_code=status.HTTP_204_NO_CONTENT)

    def present_not_found(self) -> None:
        self._response = _not_found()
