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


from app.finance.application.use_cases.list_transfers import ListTransfersRequest
from app.finance.presentation.api.v1.presenters.transfer_presenters import (
    ListTransfersHttpPresenter,
)


class ListTransfersController:
    def __init__(self, interactor_factory) -> None:
        self._factory = interactor_factory

    async def handle(self, owner_id: str, start, end) -> JSONResponse:
        presenter = ListTransfersHttpPresenter(start, end)
        await self._factory(presenter).execute(
            ListTransfersRequest(owner_id=owner_id, start=start, end=end)
        )
        return presenter.response()


from app.finance.application.use_cases.update_transfer import (
    UpdateTransferInteractor,
    UpdateTransferRequest,
)
from app.finance.presentation.api.v1.schemas.transfers import (
    UpdateTransferRequest as SchemaUpdate,
)


class UpdateTransferController:
    def __init__(
        self,
        interactor: UpdateTransferInteractor,
        presenter: __import__(
            "app.finance.presentation.api.v1.presenters.transfer_presenters",
            fromlist=["CreateTransferHttpPresenter"],
        ).CreateTransferHttpPresenter,
    ) -> None:
        self._interactor = interactor
        self._presenter = presenter

    async def handle(
        self, body: SchemaUpdate, owner_id: str, transfer_id: str
    ) -> JSONResponse:
        req = UpdateTransferRequest(
            owner_id=owner_id,
            transfer_id=transfer_id,
            from_account_id=str(body.from_account_id),
            to_account_id=str(body.to_account_id),
            amount_cents=body.amount_cents,
            description=body.description,
            occurred_on=body.occurred_on,
        )
        await self._interactor.execute(req)
        resp = self._presenter.response()
        resp.headers["Cache-Control"] = "no-store"
        return resp
