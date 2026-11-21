import uuid
from collections.abc import Callable
from dataclasses import dataclass
from datetime import date

from fastapi import Response
from fastapi.responses import JSONResponse

from app.finance.application.dtos.transfers import (
    DeleteTransferInput,
    ListTransfersInput,
)
from app.finance.application.use_cases.create_transfer import (
    CreateTransferInputPort,
    CreateTransferOutputPort,
)
from app.finance.application.use_cases.delete_transfer import (
    DeleteTransferInputPort,
    DeleteTransferOutputPort,
)
from app.finance.application.use_cases.list_transfers import (
    ListTransfersInputPort,
    ListTransfersOutputPort,
)
from app.finance.application.use_cases.update_transfer import (
    UpdateTransferInputPort,
    UpdateTransferOutputPort,
)
from app.finance.presentation.api.v1.presenters.transfer_presenters import (
    CreateTransferHttpPresenter,
    DeleteTransferHttpPresenter,
    ListTransfersHttpPresenter,
    UpdateTransferHttpPresenter,
)
from app.finance.presentation.api.v1.schemas.transfers import (
    CreateTransferRequest,
    UpdateTransferRequest,
)

CreateTransferFactory = Callable[[CreateTransferOutputPort], CreateTransferInputPort]
DeleteTransferFactory = Callable[[DeleteTransferOutputPort], DeleteTransferInputPort]
UpdateTransferFactory = Callable[[UpdateTransferOutputPort], UpdateTransferInputPort]
ListTransfersFactory = Callable[[ListTransfersOutputPort], ListTransfersInputPort]


@dataclass(frozen=True, slots=True)
class CreateTransferController:
    build_interactor: CreateTransferFactory

    async def handle(
        self, request: CreateTransferRequest, owner_id: uuid.UUID
    ) -> JSONResponse:
        presenter = CreateTransferHttpPresenter()
        await self.build_interactor(presenter).execute(request.to_input(owner_id))
        return presenter.response()


@dataclass(frozen=True, slots=True)
class DeleteTransferController:
    build_interactor: DeleteTransferFactory

    async def handle(self, owner_id: uuid.UUID, transfer_id: uuid.UUID) -> Response:
        presenter = DeleteTransferHttpPresenter()
        pedido = DeleteTransferInput(owner_id=owner_id, transfer_id=transfer_id)
        await self.build_interactor(presenter).execute(pedido)
        return presenter.response()


@dataclass(frozen=True, slots=True)
class UpdateTransferController:
    build_interactor: UpdateTransferFactory

    async def handle(
        self,
        request: UpdateTransferRequest,
        owner_id: uuid.UUID,
        transfer_id: uuid.UUID,
    ) -> JSONResponse:
        presenter = UpdateTransferHttpPresenter()
        pedido = request.to_update_input(owner_id, transfer_id)
        await self.build_interactor(presenter).execute(pedido)
        return presenter.response()


@dataclass(frozen=True, slots=True)
class ListTransfersController:
    build_interactor: ListTransfersFactory

    async def handle(self, start: date, end: date, owner_id: uuid.UUID) -> JSONResponse:
        presenter = ListTransfersHttpPresenter()
        pedido = ListTransfersInput(owner_id=owner_id, start=start, end=end)
        await self.build_interactor(presenter).execute(pedido)
        return presenter.response()
