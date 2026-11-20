from typing import Annotated

from fastapi import APIRouter, Depends, Response, status
from fastapi.responses import JSONResponse

from app.users.presentation.api.v1.controllers.authenticate_user_controller import (
    AuthenticateUserController,
)
from app.users.presentation.api.v1.controllers.logout_controller import (
    LogoutController,
)
from app.users.presentation.api.v1.controllers.refresh_session_controller import (
    RefreshSessionController,
)
from app.users.presentation.api.v1.dependencies import (
    get_authenticate_user_controller,
    get_logout_controller,
    get_refresh_session_controller,
)
from app.users.presentation.api.v1.schemas.authenticate_user import (
    AuthenticateUserRequest,
    SessionResponse,
)
from app.users.presentation.api.v1.schemas.refresh_session import (
    RefreshSessionRequest,
)

router = APIRouter(prefix="/api/v1/auth", tags=["auth"])


@router.post(
    "/login",
    response_model=SessionResponse,
    responses={
        status.HTTP_401_UNAUTHORIZED: {"description": "E-mail ou senha incorretos"},
    },
)
async def login(
    body: AuthenticateUserRequest,
    controller: Annotated[
        AuthenticateUserController, Depends(get_authenticate_user_controller)
    ],
) -> JSONResponse:
    return await controller.handle(body)


@router.post(
    "/refresh",
    response_model=SessionResponse,
    description=(
        "Troca um refresh token por um par novo (access + refresh). O refresh token "
        "usado deixa de valer; apresentá-lo de novo revoga a sessão inteira."
    ),
    responses={
        status.HTTP_401_UNAUTHORIZED: {
            "description": "Refresh token desconhecido, vencido, revogado ou já usado"
        },
    },
)
async def refresh_session(
    body: RefreshSessionRequest,
    controller: Annotated[
        RefreshSessionController, Depends(get_refresh_session_controller)
    ],
) -> JSONResponse:
    return await controller.handle(body)


@router.post(
    "/logout",
    status_code=status.HTTP_204_NO_CONTENT,
    response_class=Response,
    description=(
        "Revoga a sessão do refresh token apresentado. É idempotente: um token "
        "desconhecido também responde 204. O access token já emitido vale até vencer."
    ),
)
async def logout(
    body: RefreshSessionRequest,
    controller: Annotated[LogoutController, Depends(get_logout_controller)],
) -> Response:
    return await controller.handle(body)
