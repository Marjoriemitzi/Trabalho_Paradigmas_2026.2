from fastapi import Response, status
from fastapi.responses import JSONResponse

from app.finance.application.dtos.transfers import TransferOutput
from app.finance.application.use_cases.create_transfer import CreateTransferOutputPort
from app.finance.application.use_cases.delete_transfer import DeleteTransferOutputPort
from app.finance.presentation.api.v1.schemas.transfers import TransferResponse
from app.shared.presentation.api.errors import error_response


class CreateTransferHttpPresenter(CreateTransferOutputPort):
    def __init__(self) -> None:
        self._response: JSONResponse | None = None

    def response(self) -> JSONResponse:
        if self._response is None:
            raise RuntimeError("O caso de uso terminou sem apresentar um resultado.")
        return self._response

    def present_created(self, transfer: TransferOutput) -> None:
        corpo = TransferResponse.from_output(transfer).model_dump()
        self._response = JSONResponse(corpo, status_code=status.HTTP_201_CREATED)

    def present_invalid(self, field: str, problem: str) -> None:
        self._response = error_response(
            status.HTTP_422_UNPROCESSABLE_CONTENT,
            "invalid_transfer",
            fields=[{"field": field, "problem": problem}],
        )


class DeleteTransferHttpPresenter(DeleteTransferOutputPort):
    def __init__(self) -> None:
        self._response: Response | None = None

    def response(self) -> Response:
        if self._response is None:
            raise RuntimeError("O caso de uso terminou sem apresentar um resultado.")
        return self._response

    def present_deleted(self) -> None:
        self._response = Response(status_code=status.HTTP_204_NO_CONTENT)

    def present_not_found(self) -> None:
        self._response = error_response(status.HTTP_404_NOT_FOUND, "transfer_not_found")
