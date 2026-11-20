from typing import Annotated

from fastapi import Depends, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.shared.presentation.api.errors import ApiError
from app.users.application.ports.access_token_check import AccessTokenCheck
from app.users.application.ports.token_verifier import AuthenticatedUser, TokenVerifier

_bearer = HTTPBearer(
    auto_error=False, description="O access_token devolvido por /api/v1/auth/login"
)


def not_authenticated() -> ApiError:
    return ApiError(
        status.HTTP_401_UNAUTHORIZED,
        "not_authenticated",
        headers={"WWW-Authenticate": "Bearer"},
    )


def invalid_token() -> ApiError:
    return ApiError(
        status.HTTP_401_UNAUTHORIZED,
        "invalid_token",
        headers={"WWW-Authenticate": 'Bearer error="invalid_token"'},
    )


async def require_authenticated_user(
    request: Request,
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(_bearer)],
) -> AuthenticatedUser:
    if credentials is None:
        raise not_authenticated()
    verifier: TokenVerifier = request.app.state.token_verifier
    current = verifier.verify(credentials.credentials)
    if current is None:
        raise invalid_token()
    check: AccessTokenCheck = request.app.state.access_token_check
    if not await check.is_valid(current):
        raise invalid_token()
    return current


CurrentUser = Annotated[AuthenticatedUser, Depends(require_authenticated_user)]


def optional_authenticated_user(
    request: Request,
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(_bearer)],
) -> AuthenticatedUser | None:
    """Só identifica quem mandou um access token válido; nunca recusa o pedido."""
    if credentials is None:
        return None
    verifier: TokenVerifier = request.app.state.token_verifier
    return verifier.verify(credentials.credentials)


OptionalCurrentUser = Annotated[
    AuthenticatedUser | None, Depends(optional_authenticated_user)
]
