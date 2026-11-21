import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, Response, status
from fastapi.responses import JSONResponse

from app.finance.presentation.api.v1.controllers.recurrences_controllers import (
    CreateRecurrenceController,
    DeleteRecurrenceController,
    ListRecurrencesController,
    UpdateRecurrenceController,
)
from app.finance.presentation.api.v1.dependencies import (
    get_create_recurrence_controller,
    get_delete_recurrence_controller,
    get_list_recurrences_controller,
    get_update_recurrence_controller,
)
from app.finance.presentation.api.v1.schemas.recurrences import (
    RecurrenceListResponse,
    RecurrenceRequest,
    RecurrenceResponse,
)
from app.users.presentation.api.v1.security import CurrentUser

router = APIRouter(prefix="/api/v1/recurrences", tags=["recurrences"])


@router.post(
    "",
    status_code=status.HTTP_201_CREATED,
    response_model=RecurrenceResponse,
    description=(
        "Cadastra a regra de repetição. As transações são lançadas pelo comando "
        "diário; com `starts_on` no passado, ele lança as ocorrências atrasadas "
        "até o limite de recuperação de 62 dias."
    ),
    responses={
        status.HTTP_401_UNAUTHORIZED: {"description": "Sem token, ou token inválido"},
        status.HTTP_422_UNPROCESSABLE_CONTENT: {
            "description": "Pedido fora do formato ou com dados recusados"
        },
    },
)
async def create_recurrence(
    body: RecurrenceRequest,
    current: CurrentUser,
    controller: Annotated[
        CreateRecurrenceController, Depends(get_create_recurrence_controller)
    ],
) -> JSONResponse:
    return await controller.handle(body, owner_id=current.id.value)


@router.get(
    "",
    response_model=RecurrenceListResponse,
    description="Em ordem de próxima data (as sem data no fim) e depois por descrição.",
    responses={
        status.HTTP_401_UNAUTHORIZED: {"description": "Sem token, ou token inválido"}
    },
)
async def list_recurrences(
    current: CurrentUser,
    controller: Annotated[
        ListRecurrencesController, Depends(get_list_recurrences_controller)
    ],
) -> JSONResponse:
    return await controller.handle(owner_id=current.id.value)


@router.put(
    "/{recurrence_id}",
    response_model=RecurrenceResponse,
    description="Troca a regra inteira. Só afeta o futuro: o já lançado não muda.",
    responses={
        status.HTTP_401_UNAUTHORIZED: {"description": "Sem token, ou token inválido"},
        status.HTTP_404_NOT_FOUND: {
            "description": "A recorrência não existe entre as suas"
        },
        status.HTTP_422_UNPROCESSABLE_CONTENT: {
            "description": "Pedido fora do formato ou com dados recusados"
        },
    },
)
async def update_recurrence(
    recurrence_id: uuid.UUID,
    body: RecurrenceRequest,
    current: CurrentUser,
    controller: Annotated[
        UpdateRecurrenceController, Depends(get_update_recurrence_controller)
    ],
) -> JSONResponse:
    return await controller.handle(
        body, owner_id=current.id.value, recurrence_id=recurrence_id
    )


@router.delete(
    "/{recurrence_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    response_class=Response,
    description="Não apaga as transações que a recorrência já lançou.",
    responses={
        status.HTTP_401_UNAUTHORIZED: {"description": "Sem token, ou token inválido"},
        status.HTTP_404_NOT_FOUND: {
            "description": "A recorrência não existe entre as suas"
        },
    },
)
async def delete_recurrence(
    recurrence_id: uuid.UUID,
    current: CurrentUser,
    controller: Annotated[
        DeleteRecurrenceController, Depends(get_delete_recurrence_controller)
    ],
) -> Response:
    return await controller.handle(
        owner_id=current.id.value, recurrence_id=recurrence_id
    )
