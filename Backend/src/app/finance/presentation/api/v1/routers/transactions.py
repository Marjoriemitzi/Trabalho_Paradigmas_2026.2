import uuid
from datetime import date
from typing import Annotated

from fastapi import APIRouter, Depends, Query, Response, status
from fastapi.responses import JSONResponse

from app.finance.presentation.api.v1.controllers.change_transaction_controllers import (
    DeleteTransactionController,
    UpdateTransactionController,
)
from app.finance.presentation.api.v1.controllers.get_statement_controller import (
    GetStatementController,
)
from app.finance.presentation.api.v1.controllers.record_transaction_controller import (
    RecordTransactionController,
)
from app.finance.presentation.api.v1.dependencies import (
    get_delete_transaction_controller,
    get_record_transaction_controller,
    get_statement_controller,
    get_update_transaction_controller,
)
from app.finance.presentation.api.v1.schemas.get_statement import StatementResponse
from app.finance.presentation.api.v1.schemas.record_transaction import (
    RecordedTransactionResponse,
    RecordTransactionRequest,
    UpdateTransactionRequest,
)
from app.users.presentation.api.v1.security import CurrentUser

router = APIRouter(prefix="/api/v1/transactions", tags=["transactions"])


@router.post(
    "",
    status_code=status.HTTP_201_CREATED,
    response_model=RecordedTransactionResponse,
    responses={
        status.HTTP_401_UNAUTHORIZED: {"description": "Sem token, ou token inválido"},
        status.HTTP_422_UNPROCESSABLE_CONTENT: {
            "description": "Pedido fora do formato ou com dados recusados"
        },
    },
)
async def record_transaction(
    body: RecordTransactionRequest,
    current: CurrentUser,
    controller: Annotated[
        RecordTransactionController, Depends(get_record_transaction_controller)
    ],
) -> JSONResponse:
    return await controller.handle(body, owner_id=current.id.value)


@router.get(
    "",
    response_model=StatementResponse,
    responses={
        status.HTTP_401_UNAUTHORIZED: {"description": "Sem token, ou token inválido"},
        status.HTTP_404_NOT_FOUND: {
            "description": "A conta pedida não existe entre as suas"
        },
        status.HTTP_422_UNPROCESSABLE_CONTENT: {
            "description": "Datas ou conta fora do formato, ou período recusado"
        },
    },
)
async def get_statement(
    start: Annotated[
        date, Query(alias="from", description="Primeiro dia (AAAA-MM-DD)")
    ],
    end: Annotated[date, Query(alias="to", description="Último dia, incluído")],
    current: CurrentUser,
    controller: Annotated[GetStatementController, Depends(get_statement_controller)],
    account_id: Annotated[
        uuid.UUID | None,
        Query(description="Só esta conta; sem ele, o extrato junta todas"),
    ] = None,
) -> JSONResponse:
    return await controller.handle(
        start, end, owner_id=current.id.value, account_id=account_id
    )


@router.put(
    "/{transaction_id}",
    response_model=RecordedTransactionResponse,
    responses={
        status.HTTP_401_UNAUTHORIZED: {"description": "Sem token, ou token inválido"},
        status.HTTP_404_NOT_FOUND: {
            "description": "A transação não existe entre as suas"
        },
        status.HTTP_422_UNPROCESSABLE_CONTENT: {
            "description": "Pedido fora do formato ou com dados recusados"
        },
    },
)
async def update_transaction(
    transaction_id: uuid.UUID,
    body: UpdateTransactionRequest,
    current: CurrentUser,
    controller: Annotated[
        UpdateTransactionController, Depends(get_update_transaction_controller)
    ],
) -> JSONResponse:
    return await controller.handle(
        body, owner_id=current.id.value, transaction_id=transaction_id
    )


@router.delete(
    "/{transaction_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    response_class=Response,
    responses={
        status.HTTP_401_UNAUTHORIZED: {"description": "Sem token, ou token inválido"},
        status.HTTP_404_NOT_FOUND: {
            "description": "A transação não existe entre as suas"
        },
    },
)
async def delete_transaction(
    transaction_id: uuid.UUID,
    current: CurrentUser,
    controller: Annotated[
        DeleteTransactionController, Depends(get_delete_transaction_controller)
    ],
) -> Response:
    return await controller.handle(
        owner_id=current.id.value, transaction_id=transaction_id
    )
