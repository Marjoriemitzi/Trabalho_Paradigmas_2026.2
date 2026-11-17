from typing import Annotated

from fastapi import APIRouter, Depends, status
from fastapi.responses import JSONResponse, Response

from app.users.application.use_cases.logout_user import LogoutUserRequest
from app.users.presentation.api.v1.controllers.authenticate_user_controller import (
    AuthenticateUserController,
)
from app.users.presentation.api.v1.controllers.logout_controller import LogoutController
from app.users.presentation.api.v1.dependencies import (
    get_authenticate_user_controller,
    get_logout_controller,
)
from app.users.presentation.api.v1.schemas.authenticate_user import (
    AccessTokenResponse,
    AuthenticateUserRequest,
)
from app.users.presentation.api.v1.security import CurrentUser

router = APIRouter(prefix="/api/v1/auth", tags=["auth"])


@router.post("/login", response_model=AccessTokenResponse)
async def login(
    body: AuthenticateUserRequest,
    controller: Annotated[
        AuthenticateUserController, Depends(get_authenticate_user_controller)
    ],
) -> JSONResponse:
    return await controller.handle(body)


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
async def logout(
    current: CurrentUser,
    controller: Annotated[LogoutController, Depends(get_logout_controller)],
) -> Response:
    request = LogoutUserRequest(
        jti=current.jti, user_id=str(current.id), expires_at=current.exp
    )
    return await controller.handle(request)
