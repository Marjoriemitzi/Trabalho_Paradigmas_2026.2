from typing import Annotated

from fastapi import Depends, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.shared.presentation.api.errors import ApiError
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


def require_authenticated_user(
    request: Request,
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(_bearer)],
) -> AuthenticatedUser:
    if credentials is None:
        raise not_authenticated()
    verifier: TokenVerifier = request.app.state.token_verifier
    current = verifier.verify(credentials.credentials)
    if current is None:
        raise invalid_token()
    return current


CurrentUser = Annotated[AuthenticatedUser, Depends(require_authenticated_user)]
