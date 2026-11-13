import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, Response, status
from fastapi.responses import JSONResponse

from app.finance.presentation.api.v1.controllers.transfers_controllers import (
    CreateTransferController,
    DeleteTransferController,
)
from app.finance.presentation.api.v1.dependencies import (
    get_create_transfer_controller,
    get_delete_transfer_controller,
)
from app.finance.presentation.api.v1.schemas.transfers import (
    CreateTransferRequest,
    TransferResponse,
)
from app.users.presentation.api.v1.security import CurrentUser

router = APIRouter(prefix="/api/v1/transfers", tags=["transfers"])


@router.post(
    "",
    status_code=status.HTTP_201_CREATED,
    response_model=TransferResponse,
    responses={
        status.HTTP_401_UNAUTHORIZED: {"description": "Sem token, ou token inválido"},
        status.HTTP_422_UNPROCESSABLE_CONTENT: {
            "description": "Pedido fora do formato ou com dados recusados"
        },
    },
)
async def create_transfer(
    body: CreateTransferRequest,
    current: CurrentUser,
    controller: Annotated[
        CreateTransferController, Depends(get_create_transfer_controller)
    ],
) -> JSONResponse:
    return await controller.handle(body, owner_id=current.id.value)


@router.delete(
    "/{transfer_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    response_class=Response,
    responses={
        status.HTTP_401_UNAUTHORIZED: {"description": "Sem token, ou token inválido"},
        status.HTTP_404_NOT_FOUND: {
            "description": "A transferência não existe entre as suas"
        },
    },
)
async def delete_transfer(
    transfer_id: uuid.UUID,
    current: CurrentUser,
    controller: Annotated[
        DeleteTransferController, Depends(get_delete_transfer_controller)
    ],
) -> Response:
    return await controller.handle(owner_id=current.id.value, transfer_id=transfer_id)
