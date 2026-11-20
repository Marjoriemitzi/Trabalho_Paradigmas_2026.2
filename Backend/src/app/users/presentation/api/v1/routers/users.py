from typing import Annotated

from fastapi import APIRouter, Depends, Response, status
from fastapi.responses import JSONResponse

from app.users.presentation.api.v1.controllers.change_password_controller import (
    ChangePasswordController,
)
from app.users.presentation.api.v1.controllers.delete_user_controller import (
    DeleteUserController,
)
from app.users.presentation.api.v1.controllers.get_current_user_controller import (
    GetCurrentUserController,
)
from app.users.presentation.api.v1.controllers.register_user_controller import (
    RegisterUserController,
)
from app.users.presentation.api.v1.dependencies import (
    get_change_password_controller,
    get_current_user_controller,
    get_delete_user_controller,
    get_register_user_controller,
)
from app.users.presentation.api.v1.schemas.change_password import (
    ChangePasswordRequest,
)
from app.users.presentation.api.v1.schemas.delete_user import DeleteUserRequest
from app.users.presentation.api.v1.schemas.get_current_user import (
    UserProfileResponse,
)
from app.users.presentation.api.v1.schemas.register_user import (
    RegisteredUserResponse,
    RegisterUserRequest,
)
from app.users.presentation.api.v1.security import CurrentUser

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


@router.get(
    "/me",
    response_model=UserProfileResponse,
    responses={
        status.HTTP_401_UNAUTHORIZED: {
            "description": "Sem token, ou com um token inválido ou expirado"
        },
    },
)
async def get_current_user(
    current: CurrentUser,
    controller: Annotated[
        GetCurrentUserController, Depends(get_current_user_controller)
    ],
) -> JSONResponse:
    return await controller.handle(current)


@router.post(
    "/me/password",
    status_code=status.HTTP_204_NO_CONTENT,
    description=(
        "Troca a senha de quem está logado. Os tokens já emitidos continuam valendo "
        "até expirarem (`JWT_EXPIRES_MINUTES`); a revogação fica para o refresh token."
    ),
    responses={
        status.HTTP_401_UNAUTHORIZED: {
            "description": "Sem token, ou com um token inválido ou expirado"
        },
        status.HTTP_422_UNPROCESSABLE_CONTENT: {
            "description": "Senha atual errada, senha nova fraca ou pedido mal formado"
        },
    },
)
async def change_password(
    body: ChangePasswordRequest,
    current: CurrentUser,
    controller: Annotated[
        ChangePasswordController, Depends(get_change_password_controller)
    ],
) -> Response:
    return await controller.handle(body, current)


@router.delete(
    "/me",
    status_code=status.HTTP_204_NO_CONTENT,
    description=(
        "Apaga a conta de quem está logado e, em cascata, contas, transações e "
        "transferências. Confirma com a senha atual, enviada no corpo do DELETE."
    ),
    responses={
        status.HTTP_401_UNAUTHORIZED: {
            "description": "Sem token, token inválido ou usuário já apagado"
        },
        status.HTTP_422_UNPROCESSABLE_CONTENT: {
            "description": "Senha atual errada ou pedido mal formado"
        },
    },
)
async def delete_user(
    body: DeleteUserRequest,
    current: CurrentUser,
    controller: Annotated[DeleteUserController, Depends(get_delete_user_controller)],
) -> Response:
    return await controller.handle(body, current)
