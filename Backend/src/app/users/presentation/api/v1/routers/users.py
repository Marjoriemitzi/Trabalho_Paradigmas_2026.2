from typing import Annotated

from fastapi import APIRouter, Depends, status
from fastapi.responses import JSONResponse

from app.users.presentation.api.v1.controllers.register_user_controller import (
    RegisterUserController,
)
from app.users.presentation.api.v1.dependencies import get_register_user_controller
from app.users.presentation.api.v1.schemas.register_user import (
    RegisteredUserResponse,
    RegisterUserRequest,
)

router = APIRouter(prefix="/api/v1/users", tags=["users"])


@router.post(
    "",
    status_code=status.HTTP_201_CREATED,
    response_model=RegisteredUserResponse,
    responses={
        status.HTTP_409_CONFLICT: {"description": "E-mail já cadastrado"},
        status.HTTP_422_UNPROCESSABLE_CONTENT: {
            "description": "E-mail inválido, senha fraca ou pedido mal formado"
        },
    },
)
async def register_user(
    body: RegisterUserRequest,
    controller: Annotated[
        RegisterUserController, Depends(get_register_user_controller)
    ],
) -> JSONResponse:
    return await controller.handle(body)
