import uuid
from collections.abc import Callable
from dataclasses import dataclass
from datetime import date

from fastapi.responses import JSONResponse

from app.finance.application.dtos.get_statement import GetStatementInput
from app.finance.application.use_cases.get_statement import (
    GetStatementInputPort,
    GetStatementOutputPort,
)
from app.finance.presentation.api.v1.presenters.get_statement_presenter import (
    GetStatementHttpPresenter,
)

GetStatementFactory = Callable[[GetStatementOutputPort], GetStatementInputPort]


@dataclass(frozen=True, slots=True)
class GetStatementController:
    build_interactor: GetStatementFactory

    async def handle(
        self,
        start: date,
        end: date,
        owner_id: uuid.UUID,
        account_id: uuid.UUID | None = None,
    ) -> JSONResponse:
        presenter = GetStatementHttpPresenter()
        pedido = GetStatementInput(
            owner_id=owner_id, start=start, end=end, account_id=account_id
        )
        await self.build_interactor(presenter).execute(pedido)
        return presenter.response()
