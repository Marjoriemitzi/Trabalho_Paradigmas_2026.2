from typing import override

from fastapi import Response, status
from fastapi.responses import JSONResponse

from app.finance.application.dtos.transfers import TransferListOutput, TransferOutput
from app.finance.application.use_cases.create_transfer import CreateTransferOutputPort
from app.finance.application.use_cases.delete_transfer import DeleteTransferOutputPort
from app.finance.application.use_cases.list_transfers import ListTransfersOutputPort
from app.finance.application.use_cases.update_transfer import UpdateTransferOutputPort
from app.finance.presentation.api.v1.schemas.transfers import (
    TransferListResponse,
    TransferResponse,
)
from app.shared.presentation.api.errors import error_response


class CreateTransferHttpPresenter(CreateTransferOutputPort):
    def __init__(self) -> None:
        self._response: JSONResponse | None = None

    def response(self) -> JSONResponse:
        if self._response is None:
            raise RuntimeError("O caso de uso terminou sem apresentar um resultado.")
        return self._response

    @override
    def present_created(self, transfer: TransferOutput) -> None:
        corpo = TransferResponse.from_output(transfer).model_dump()
        self._response = JSONResponse(corpo, status_code=status.HTTP_201_CREATED)

    @override
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

    @override
    def present_deleted(self) -> None:
        self._response = Response(status_code=status.HTTP_204_NO_CONTENT)

    @override
    def present_not_found(self) -> None:
        self._response = error_response(status.HTTP_404_NOT_FOUND, "transfer_not_found")


class UpdateTransferHttpPresenter(UpdateTransferOutputPort):
    def __init__(self) -> None:
        self._response: JSONResponse | None = None

    def response(self) -> JSONResponse:
        if self._response is None:
            raise RuntimeError("O caso de uso terminou sem apresentar um resultado.")
        return self._response

    @override
    def present_updated(self, transfer: TransferOutput) -> None:
        corpo = TransferResponse.from_output(transfer).model_dump()
        self._response = JSONResponse(
            corpo,
            status_code=status.HTTP_200_OK,
            headers={"Cache-Control": "no-store"},
        )

    @override
    def present_invalid(self, field: str, problem: str) -> None:
        self._response = error_response(
            status.HTTP_422_UNPROCESSABLE_CONTENT,
            "invalid_transfer",
            fields=[{"field": field, "problem": problem}],
        )

    @override
    def present_not_found(self) -> None:
        self._response = error_response(status.HTTP_404_NOT_FOUND, "transfer_not_found")


class ListTransfersHttpPresenter(ListTransfersOutputPort):
    def __init__(self) -> None:
        self._response: JSONResponse | None = None

    def response(self) -> JSONResponse:
        if self._response is None:
            raise RuntimeError("O caso de uso terminou sem apresentar um resultado.")
        return self._response

    @override
    def present_listed(self, listing: TransferListOutput) -> None:
        corpo = TransferListResponse.from_output(listing).model_dump(by_alias=True)
        self._response = JSONResponse(
            corpo,
            status_code=status.HTTP_200_OK,
            headers={"Cache-Control": "no-store"},
        )

    @override
    def present_invalid(self, field: str, problem: str) -> None:
        self._response = error_response(
            status.HTTP_422_UNPROCESSABLE_CONTENT,
            "invalid_period",
            fields=[{"field": field, "problem": problem}],
        )
