import uuid
from collections.abc import Callable
from dataclasses import dataclass

from fastapi import Response
from fastapi.responses import JSONResponse

from app.finance.application.dtos.transfers import DeleteTransferInput
from app.finance.application.use_cases.create_transfer import (
    CreateTransferInputPort,
    CreateTransferOutputPort,
)
from app.finance.application.use_cases.delete_transfer import (
    DeleteTransferInputPort,
    DeleteTransferOutputPort,
)
from app.finance.presentation.api.v1.presenters.transfer_presenters import (
    CreateTransferHttpPresenter,
    DeleteTransferHttpPresenter,
)
from app.finance.presentation.api.v1.schemas.transfers import CreateTransferRequest

CreateTransferFactory = Callable[[CreateTransferOutputPort], CreateTransferInputPort]
DeleteTransferFactory = Callable[[DeleteTransferOutputPort], DeleteTransferInputPort]


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
