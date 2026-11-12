from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.responses import JSONResponse
from fastapi.security import OAuth2PasswordBearer

from app.users.infrastructure.persistence.repositories.sqlalchemy_token_blocklist_repository import (
    SQLAlchemyTokenBlocklistRepository,
)
from app.users.presentation.api.v1.controllers.get_current_user_controller import (
    GetCurrentUserController,
)
from app.users.presentation.api.v1.controllers.register_user_controller import (
    RegisterUserController,
)
from app.users.presentation.api.v1.dependencies import (
    get_current_user_controller,
    get_register_user_controller,
)
from app.users.presentation.api.v1.schemas.get_current_user import (
    UserProfileResponse,
)
from app.users.presentation.api.v1.schemas.register_user import (
    RegisteredUserResponse,
    RegisterUserRequest,
)
from app.users.presentation.api.v1.security import CurrentUser

router = APIRouter(prefix="/api/v1/users", tags=["users"])
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")


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
    request: Request,
    current: CurrentUser,
    controller: Annotated[
        GetCurrentUserController, Depends(get_current_user_controller)
    ],
    token: Annotated[str, Depends(oauth2_scheme)],
) -> JSONResponse:
    session_factory = request.app.state.session_factory
    async with session_factory() as session:
        blocklist_repo = SQLAlchemyTokenBlocklistRepository(session)
        is_blocked = await blocklist_repo.is_blocked(token)

    if is_blocked:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Sessão encerrada. Faça login novamente.",
        )

    return await controller.handle(current)
