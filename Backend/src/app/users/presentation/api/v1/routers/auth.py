"""Rotas de autenticação. Só ligam cada caminho ao seu controller."""

from typing import Annotated

from fastapi import APIRouter, Depends, status
from fastapi.responses import JSONResponse, Response
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncSession

# Import do banco de dados (ajuste se a função get_session tiver outro nome no seu projeto)
from app.shared.infrastructure.persistence.database import get_session

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

# Injeção de dependência local para o Logout (pode ser movida para dependencies.py futuramente)
async def get_logout_interactor(
    session: AsyncSession = Depends(get_session),
) -> LogoutUserInteractor:
    repo = SQLAlchemyTokenBlocklistRepository(session)
    return LogoutUserInteractor(repo)


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