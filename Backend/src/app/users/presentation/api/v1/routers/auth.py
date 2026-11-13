from typing import Annotated

from fastapi import APIRouter, Depends, status
from fastapi.responses import JSONResponse

from app.users.presentation.api.v1.controllers.authenticate_user_controller import (
    AuthenticateUserController,
)
from app.users.presentation.api.v1.dependencies import (
    get_authenticate_user_controller,
)
from app.users.presentation.api.v1.schemas.authenticate_user import (
    AccessTokenResponse,
    AuthenticateUserRequest,
)

router = APIRouter(prefix="/api/v1/auth", tags=["auth"])


@router.post(
    "/login",
    response_model=AccessTokenResponse,
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
