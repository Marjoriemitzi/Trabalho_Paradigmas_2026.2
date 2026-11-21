import uuid
from collections.abc import Callable
from dataclasses import dataclass

from fastapi import Response
from fastapi.responses import JSONResponse

from app.finance.application.dtos.recurrences import (
    DeleteRecurrenceInput,
    ListRecurrencesInput,
)
from app.finance.application.use_cases.create_recurrence import (
    CreateRecurrenceInputPort,
    CreateRecurrenceOutputPort,
)
from app.finance.application.use_cases.delete_recurrence import (
    DeleteRecurrenceInputPort,
    DeleteRecurrenceOutputPort,
)
from app.finance.application.use_cases.list_recurrences import (
    ListRecurrencesInputPort,
    ListRecurrencesOutputPort,
)
from app.finance.application.use_cases.update_recurrence import (
    UpdateRecurrenceInputPort,
    UpdateRecurrenceOutputPort,
)
from app.finance.presentation.api.v1.presenters.recurrence_presenters import (
    CreateRecurrenceHttpPresenter,
    DeleteRecurrenceHttpPresenter,
    ListRecurrencesHttpPresenter,
    UpdateRecurrenceHttpPresenter,
)
from app.finance.presentation.api.v1.schemas.recurrences import RecurrenceRequest

CreateRecurrenceFactory = Callable[
    [CreateRecurrenceOutputPort], CreateRecurrenceInputPort
]
UpdateRecurrenceFactory = Callable[
    [UpdateRecurrenceOutputPort], UpdateRecurrenceInputPort
]
DeleteRecurrenceFactory = Callable[
    [DeleteRecurrenceOutputPort], DeleteRecurrenceInputPort
]
ListRecurrencesFactory = Callable[[ListRecurrencesOutputPort], ListRecurrencesInputPort]


@dataclass(frozen=True, slots=True)
class CreateRecurrenceController:
    build_interactor: CreateRecurrenceFactory

    async def handle(
        self, request: RecurrenceRequest, owner_id: uuid.UUID
    ) -> JSONResponse:
        presenter = CreateRecurrenceHttpPresenter()
        await self.build_interactor(presenter).execute(request.to_input(owner_id))
        return presenter.response()


@dataclass(frozen=True, slots=True)
class UpdateRecurrenceController:
    build_interactor: UpdateRecurrenceFactory

    async def handle(
        self,
        request: RecurrenceRequest,
        owner_id: uuid.UUID,
        recurrence_id: uuid.UUID,
    ) -> JSONResponse:
        presenter = UpdateRecurrenceHttpPresenter()
        pedido = request.to_update_input(owner_id, recurrence_id)
        await self.build_interactor(presenter).execute(pedido)
        return presenter.response()


@dataclass(frozen=True, slots=True)
class DeleteRecurrenceController:
    build_interactor: DeleteRecurrenceFactory

    async def handle(self, owner_id: uuid.UUID, recurrence_id: uuid.UUID) -> Response:
        presenter = DeleteRecurrenceHttpPresenter()
        pedido = DeleteRecurrenceInput(owner_id=owner_id, recurrence_id=recurrence_id)
        await self.build_interactor(presenter).execute(pedido)
        return presenter.response()


@dataclass(frozen=True, slots=True)
class ListRecurrencesController:
    build_interactor: ListRecurrencesFactory

    async def handle(self, owner_id: uuid.UUID) -> JSONResponse:
        presenter = ListRecurrencesHttpPresenter()
        await self.build_interactor(presenter).execute(
            ListRecurrencesInput(owner_id=owner_id)
        )
        return presenter.response()
