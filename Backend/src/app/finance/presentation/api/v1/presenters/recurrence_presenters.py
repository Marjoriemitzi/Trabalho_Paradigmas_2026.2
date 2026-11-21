from typing import override

from fastapi import Response, status
from fastapi.responses import JSONResponse

from app.finance.application.dtos.recurrences import RecurrenceOutput
from app.finance.application.use_cases.create_recurrence import (
    CreateRecurrenceOutputPort,
)
from app.finance.application.use_cases.delete_recurrence import (
    DeleteRecurrenceOutputPort,
)
from app.finance.application.use_cases.list_recurrences import (
    ListRecurrencesOutputPort,
)
from app.finance.application.use_cases.update_recurrence import (
    UpdateRecurrenceOutputPort,
)
from app.finance.presentation.api.v1.schemas.recurrences import (
    RecurrenceListResponse,
    RecurrenceResponse,
)
from app.shared.presentation.api.errors import error_response

_NO_STORE = {"Cache-Control": "no-store"}


def _invalid(field: str, problem: str) -> JSONResponse:
    return error_response(
        status.HTTP_422_UNPROCESSABLE_CONTENT,
        "invalid_recurrence",
        fields=[{"field": field, "problem": problem}],
    )


class CreateRecurrenceHttpPresenter(CreateRecurrenceOutputPort):
    def __init__(self) -> None:
        self._response: JSONResponse | None = None

    def response(self) -> JSONResponse:
        if self._response is None:
            raise RuntimeError("O caso de uso terminou sem apresentar um resultado.")
        return self._response

    @override
    def present_created(self, recurrence: RecurrenceOutput) -> None:
        corpo = RecurrenceResponse.from_output(recurrence).model_dump()
        self._response = JSONResponse(
            corpo, status_code=status.HTTP_201_CREATED, headers=_NO_STORE
        )

    @override
    def present_invalid(self, field: str, problem: str) -> None:
        self._response = _invalid(field, problem)


class UpdateRecurrenceHttpPresenter(UpdateRecurrenceOutputPort):
    def __init__(self) -> None:
        self._response: JSONResponse | None = None

    def response(self) -> JSONResponse:
        if self._response is None:
            raise RuntimeError("O caso de uso terminou sem apresentar um resultado.")
        return self._response

    @override
    def present_updated(self, recurrence: RecurrenceOutput) -> None:
        corpo = RecurrenceResponse.from_output(recurrence).model_dump()
        self._response = JSONResponse(
            corpo, status_code=status.HTTP_200_OK, headers=_NO_STORE
        )

    @override
    def present_invalid(self, field: str, problem: str) -> None:
        self._response = _invalid(field, problem)

    @override
    def present_not_found(self) -> None:
        self._response = error_response(
            status.HTTP_404_NOT_FOUND, "recurrence_not_found"
        )


class DeleteRecurrenceHttpPresenter(DeleteRecurrenceOutputPort):
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
        self._response = error_response(
            status.HTTP_404_NOT_FOUND, "recurrence_not_found"
        )


class ListRecurrencesHttpPresenter(ListRecurrencesOutputPort):
    def __init__(self) -> None:
        self._response: JSONResponse | None = None

    def response(self) -> JSONResponse:
        if self._response is None:
            raise RuntimeError("O caso de uso terminou sem apresentar um resultado.")
        return self._response

    @override
    def present_listed(self, recurrences: list[RecurrenceOutput]) -> None:
        corpo = RecurrenceListResponse(
            recurrences=[RecurrenceResponse.from_output(r) for r in recurrences]
        ).model_dump()
        self._response = JSONResponse(
            corpo, status_code=status.HTTP_200_OK, headers=_NO_STORE
        )
