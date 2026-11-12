"""Rotas de autenticação. Só ligam cada caminho ao seu controller."""

from collections.abc import AsyncIterator
from typing import Annotated

from fastapi import APIRouter, Depends, Request, status
from fastapi.responses import JSONResponse, Response
from fastapi.security import OAuth2PasswordBearer

from app.users.application.use_cases.logout_user_interactor import (
    LogoutUserInteractor,
)
from app.users.infrastructure.persistence.repositories.sqlalchemy_token_blocklist_repository import (
    SQLAlchemyTokenBlocklistRepository,
)
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
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")


async def get_logout_interactor(
    request: Request,
) -> AsyncIterator[LogoutUserInteractor]:
    session_factory = request.app.state.session_factory
    async with session_factory() as session:
        repo = SQLAlchemyTokenBlocklistRepository(session)
        yield LogoutUserInteractor(repo)


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


@router.post(
    "/logout",
    status_code=status.HTTP_204_NO_CONTENT,
    responses={
        status.HTTP_401_UNAUTHORIZED: {"description": "Não autenticado"},
    },
)
async def logout(
    token: Annotated[str, Depends(oauth2_scheme)],
    interactor: Annotated[LogoutUserInteractor, Depends(get_logout_interactor)],
) -> Response:
    await interactor.execute(token)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
