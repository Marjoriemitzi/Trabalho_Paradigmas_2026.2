from typing import Annotated

from fastapi import Depends, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.users.application.ports.token_verifier import AuthenticatedUser, TokenVerifier

_bearer = HTTPBearer(
    auto_error=False, description="O access_token devolvido por /api/v1/auth/login"
)


def not_authenticated() -> HTTPException:
    return HTTPException(
        status.HTTP_401_UNAUTHORIZED,
        detail="not_authenticated",
        headers={"WWW-Authenticate": "Bearer"},
    )


def invalid_token() -> HTTPException:
    return HTTPException(
        status.HTTP_401_UNAUTHORIZED,
        detail="invalid_token",
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
