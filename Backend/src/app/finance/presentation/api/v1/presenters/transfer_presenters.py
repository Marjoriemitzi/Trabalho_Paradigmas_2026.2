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


from app.finance.application.use_cases.list_transfers import ListTransfersOutputPort


class ListTransfersHttpPresenter(ListTransfersOutputPort):
    def __init__(self, start, end) -> None:
        self.start = start
        self.end = end
        self._response: JSONResponse | None = None

    def response(self) -> JSONResponse:
        if self._response is None:
            raise RuntimeError()
        return self._response

    def present_listed(self, transfers: list) -> None:
        from app.finance.presentation.api.v1.schemas.transfers import (
            TransferListResponse,
        )

        resp = TransferListResponse(
            start_date=self.start,
            end_date=self.end,
            transfers=[t.__dict__ for t in transfers],
        ).model_dump(by_alias=True)
        self._response = JSONResponse(resp, headers={"Cache-Control": "no-store"})

    def present_invalid_period(self, problems: list[dict[str, str]]) -> None:
        self._response = error_response(
            status.HTTP_422_UNPROCESSABLE_CONTENT, "invalid_period", fields=problems
        )
