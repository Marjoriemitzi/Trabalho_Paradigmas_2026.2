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


from app.finance.application.use_cases.rename_account import RenameAccountInteractor
from app.finance.application.use_cases.rename_account import (
    RenameAccountRequest as RenameDto,
)
from app.finance.presentation.api.v1.schemas.accounts import RenameAccountRequest


class RenameAccountController:
    def __init__(
        self,
        interactor: RenameAccountInteractor,
        presenter: __import__(
            "app.finance.presentation.api.v1.presenters.create_account_presenter",
            fromlist=["CreateAccountHttpPresenter"],
        ).CreateAccountHttpPresenter,
    ) -> None:
        self._interactor = interactor
        self._presenter = presenter

    async def handle(
        self, body: RenameAccountRequest, owner_id: str, account_id: str
    ) -> JSONResponse:
        await self._interactor.execute(
            RenameDto(owner_id=owner_id, account_id=account_id, name=body.name)
        )
        return self._presenter.response()


from app.finance.application.use_cases.delete_account import DeleteAccountInteractor
from app.finance.application.use_cases.delete_account import (
    DeleteAccountRequest as DeleteDto,
)
from app.finance.presentation.api.v1.presenters.delete_account_presenter import (
    DeleteAccountHttpPresenter,
)


class DeleteAccountController:
    def __init__(
        self, interactor: DeleteAccountInteractor, presenter: DeleteAccountHttpPresenter
    ) -> None:
        self._interactor = interactor
        self._presenter = presenter

    async def handle(self, owner_id: str, account_id: str) -> JSONResponse:
        await self._interactor.execute(
            DeleteDto(owner_id=owner_id, account_id=account_id)
        )
        return self._presenter.response()
