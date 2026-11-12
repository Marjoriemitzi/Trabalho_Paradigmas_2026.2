from typing import Annotated

from fastapi import APIRouter, Depends, status
from fastapi.responses import JSONResponse

from app.finance.presentation.api.v1.controllers.accounts_controllers import (
    CreateAccountController,
    ListAccountsController,
)
from app.finance.presentation.api.v1.dependencies import (
    get_create_account_controller,
    get_list_accounts_controller,
)
from app.finance.presentation.api.v1.schemas.accounts import (
    AccountListResponse,
    AccountResponse,
    CreateAccountRequest,
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
