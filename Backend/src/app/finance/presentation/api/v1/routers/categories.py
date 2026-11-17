from typing import Annotated

from fastapi import APIRouter, Depends, status
from fastapi.responses import JSONResponse

from app.finance.presentation.api.v1.controllers.categories_controller import (
    ListCategoriesController,
)
from app.finance.presentation.api.v1.dependencies import (
    get_list_categories_controller,
)
from app.finance.presentation.api.v1.schemas.categories import CategoryListResponse
from app.users.presentation.api.v1.security import CurrentUser

router = APIRouter(prefix="/api/v1/categories", tags=["categories"])


@router.get(
    "",
    response_model=CategoryListResponse,
    responses={
        status.HTTP_401_UNAUTHORIZED: {"description": "Sem token, ou token inválido"},
    },
)
async def list_categories(
    current: CurrentUser,
    controller: Annotated[
        ListCategoriesController, Depends(get_list_categories_controller)
    ],
) -> JSONResponse:
    return await controller.handle()
