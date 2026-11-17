import uuid
from collections.abc import Callable
from dataclasses import dataclass

from fastapi.responses import JSONResponse

from app.finance.application.dtos.list_accounts import ListAccountsInput
from app.finance.application.use_cases.create_account import (
    CreateAccountInputPort,
    CreateAccountOutputPort,
)
from app.finance.application.use_cases.list_accounts import (
    ListAccountsInputPort,
    ListAccountsOutputPort,
)
from app.finance.presentation.api.v1.presenters.create_account_presenter import (
    CreateAccountHttpPresenter,
)
from app.finance.presentation.api.v1.presenters.list_accounts_presenter import (
    ListAccountsHttpPresenter,
)
from app.finance.presentation.api.v1.schemas.accounts import CreateAccountRequest

CreateAccountFactory = Callable[[CreateAccountOutputPort], CreateAccountInputPort]
ListAccountsFactory = Callable[[ListAccountsOutputPort], ListAccountsInputPort]


@dataclass(frozen=True, slots=True)
class CreateAccountController:
    build_interactor: CreateAccountFactory

    async def handle(
        self, request: CreateAccountRequest, owner_id: uuid.UUID
    ) -> JSONResponse:
        presenter = CreateAccountHttpPresenter()
        await self.build_interactor(presenter).execute(request.to_input(owner_id))
        return presenter.response()


@dataclass(frozen=True, slots=True)
class ListAccountsController:
    build_interactor: ListAccountsFactory

    async def handle(self, owner_id: uuid.UUID) -> JSONResponse:
        presenter = ListAccountsHttpPresenter()
        pedido = ListAccountsInput(owner_id=owner_id)
        await self.build_interactor(presenter).execute(pedido)
        return presenter.response()
