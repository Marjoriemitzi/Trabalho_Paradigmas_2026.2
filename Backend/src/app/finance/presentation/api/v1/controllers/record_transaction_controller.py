import uuid
from collections.abc import Callable
from dataclasses import dataclass

from fastapi.responses import JSONResponse

from app.finance.application.use_cases.record_transaction import (
    RecordTransactionInputPort,
    RecordTransactionOutputPort,
)
from app.finance.presentation.api.v1.presenters.record_transaction_presenter import (
    RecordTransactionHttpPresenter,
)
from app.finance.presentation.api.v1.schemas.record_transaction import (
    RecordTransactionRequest,
)

RecordTransactionFactory = Callable[
    [RecordTransactionOutputPort], RecordTransactionInputPort
]


@dataclass(frozen=True, slots=True)
class RecordTransactionController:
    build_interactor: RecordTransactionFactory

    async def handle(
        self, request: RecordTransactionRequest, owner_id: uuid.UUID
    ) -> JSONResponse:
        presenter = RecordTransactionHttpPresenter()
        await self.build_interactor(presenter).execute(request.to_input(owner_id))
        return presenter.response()
