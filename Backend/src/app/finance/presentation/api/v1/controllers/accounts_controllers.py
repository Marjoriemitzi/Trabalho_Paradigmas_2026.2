import uuid
from collections.abc import Callable
from dataclasses import dataclass

from fastapi import Response
from fastapi.responses import JSONResponse

from app.finance.application.dtos.delete_account import DeleteAccountInput
from app.finance.application.dtos.list_accounts import ListAccountsInput
from app.finance.application.use_cases.create_account import (
    CreateAccountInputPort,
    CreateAccountOutputPort,
)
from app.finance.application.use_cases.delete_account import (
    DeleteAccountInputPort,
    DeleteAccountOutputPort,
)
from app.finance.application.use_cases.list_accounts import (
    ListAccountsInputPort,
    ListAccountsOutputPort,
)
from app.finance.application.use_cases.rename_account import (
    RenameAccountInputPort,
    RenameAccountOutputPort,
)
from app.finance.presentation.api.v1.presenters.create_account_presenter import (
    CreateAccountHttpPresenter,
)
from app.finance.presentation.api.v1.presenters.delete_account_presenter import (
    DeleteAccountHttpPresenter,
)
from app.finance.presentation.api.v1.presenters.list_accounts_presenter import (
    ListAccountsHttpPresenter,
)
from app.finance.presentation.api.v1.presenters.rename_account_presenter import (
    RenameAccountHttpPresenter,
)
from app.finance.presentation.api.v1.schemas.accounts import (
    CreateAccountRequest,
    RenameAccountRequest,
)

CreateAccountFactory = Callable[[CreateAccountOutputPort], CreateAccountInputPort]
ListAccountsFactory = Callable[[ListAccountsOutputPort], ListAccountsInputPort]
RenameAccountFactory = Callable[[RenameAccountOutputPort], RenameAccountInputPort]
DeleteAccountFactory = Callable[[DeleteAccountOutputPort], DeleteAccountInputPort]


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


@dataclass(frozen=True, slots=True)
class RenameAccountController:
    build_interactor: RenameAccountFactory

    async def handle(
        self,
        request: RenameAccountRequest,
        owner_id: uuid.UUID,
        account_id: uuid.UUID,
    ) -> JSONResponse:
        presenter = RenameAccountHttpPresenter()
        pedido = request.to_input(owner_id, account_id)
        await self.build_interactor(presenter).execute(pedido)
        return presenter.response()


@dataclass(frozen=True, slots=True)
class DeleteAccountController:
    build_interactor: DeleteAccountFactory

    async def handle(self, owner_id: uuid.UUID, account_id: uuid.UUID) -> Response:
        presenter = DeleteAccountHttpPresenter()
        pedido = DeleteAccountInput(owner_id=owner_id, account_id=account_id)
        await self.build_interactor(presenter).execute(pedido)
        return presenter.response()
