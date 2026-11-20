import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, Response, status
from fastapi.responses import JSONResponse

from app.finance.presentation.api.v1.controllers.accounts_controllers import (
    CreateAccountController,
    DeleteAccountController,
    ListAccountsController,
    RenameAccountController,
)
from app.finance.presentation.api.v1.dependencies import (
    get_create_account_controller,
    get_delete_account_controller,
    get_list_accounts_controller,
    get_rename_account_controller,
)
from app.finance.presentation.api.v1.schemas.accounts import (
    AccountListResponse,
    AccountResponse,
    CreateAccountRequest,
    RenameAccountRequest,
)
from app.users.presentation.api.v1.security import CurrentUser

router = APIRouter(prefix="/api/v1/accounts", tags=["accounts"])


@router.post(
    "",
    status_code=status.HTTP_201_CREATED,
    response_model=AccountResponse,
    responses={
        status.HTTP_401_UNAUTHORIZED: {"description": "Sem token, ou token inválido"},
        status.HTTP_409_CONFLICT: {"description": "Já existe uma conta com esse nome"},
        status.HTTP_422_UNPROCESSABLE_CONTENT: {
            "description": "Pedido fora do formato ou com dados recusados"
        },
    },
)
async def create_account(
    body: CreateAccountRequest,
    current: CurrentUser,
    controller: Annotated[
        CreateAccountController, Depends(get_create_account_controller)
    ],
) -> JSONResponse:
    return await controller.handle(body, owner_id=current.id.value)


@router.get(
    "",
    response_model=AccountListResponse,
    responses={
        status.HTTP_401_UNAUTHORIZED: {"description": "Sem token, ou token inválido"},
    },
)
async def list_accounts(
    current: CurrentUser,
    controller: Annotated[
        ListAccountsController, Depends(get_list_accounts_controller)
    ],
) -> JSONResponse:
    return await controller.handle(owner_id=current.id.value)


@router.patch(
    "/{account_id}",
    response_model=AccountResponse,
    responses={
        status.HTTP_401_UNAUTHORIZED: {"description": "Sem token, ou token inválido"},
        status.HTTP_404_NOT_FOUND: {"description": "A conta não existe entre as suas"},
        status.HTTP_409_CONFLICT: {"description": "Já existe uma conta com esse nome"},
        status.HTTP_422_UNPROCESSABLE_CONTENT: {
            "description": "Pedido fora do formato ou com dados recusados"
        },
    },
)
async def rename_account(
    account_id: uuid.UUID,
    body: RenameAccountRequest,
    current: CurrentUser,
    controller: Annotated[
        RenameAccountController, Depends(get_rename_account_controller)
    ],
) -> JSONResponse:
    return await controller.handle(
        body, owner_id=current.id.value, account_id=account_id
    )


@router.delete(
    "/{account_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    response_class=Response,
    responses={
        status.HTTP_401_UNAUTHORIZED: {"description": "Sem token, ou token inválido"},
        status.HTTP_404_NOT_FOUND: {"description": "A conta não existe entre as suas"},
        status.HTTP_409_CONFLICT: {
            "description": "A conta tem transações ou transferências"
        },
    },
)
async def delete_account(
    account_id: uuid.UUID,
    current: CurrentUser,
    controller: Annotated[
        DeleteAccountController, Depends(get_delete_account_controller)
    ],
) -> Response:
    return await controller.handle(owner_id=current.id.value, account_id=account_id)
