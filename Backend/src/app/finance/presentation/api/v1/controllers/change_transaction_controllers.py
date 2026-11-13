import uuid
from collections.abc import Callable
from dataclasses import dataclass

from fastapi import Response
from fastapi.responses import JSONResponse

from app.finance.application.dtos.change_transaction import DeleteTransactionInput
from app.finance.application.use_cases.delete_transaction import (
    DeleteTransactionInputPort,
    DeleteTransactionOutputPort,
)
from app.finance.application.use_cases.update_transaction import (
    UpdateTransactionInputPort,
    UpdateTransactionOutputPort,
)
from app.finance.presentation.api.v1.presenters.change_transaction_presenters import (
    DeleteTransactionHttpPresenter,
    UpdateTransactionHttpPresenter,
)
from app.finance.presentation.api.v1.schemas.record_transaction import (
    UpdateTransactionRequest,
)

UpdateTransactionFactory = Callable[
    [UpdateTransactionOutputPort], UpdateTransactionInputPort
]
DeleteTransactionFactory = Callable[
    [DeleteTransactionOutputPort], DeleteTransactionInputPort
]


@dataclass(frozen=True, slots=True)
class UpdateTransactionController:
    build_interactor: UpdateTransactionFactory

    async def handle(
        self,
        request: UpdateTransactionRequest,
        owner_id: uuid.UUID,
        transaction_id: uuid.UUID,
    ) -> JSONResponse:
        presenter = UpdateTransactionHttpPresenter()
        pedido = request.to_update_input(owner_id, transaction_id)
        await self.build_interactor(presenter).execute(pedido)
        return presenter.response()


@dataclass(frozen=True, slots=True)
class DeleteTransactionController:
    build_interactor: DeleteTransactionFactory

    async def handle(self, owner_id: uuid.UUID, transaction_id: uuid.UUID) -> Response:
        presenter = DeleteTransactionHttpPresenter()
        pedido = DeleteTransactionInput(
            owner_id=owner_id, transaction_id=transaction_id
        )
        await self.build_interactor(presenter).execute(pedido)
        return presenter.response()
