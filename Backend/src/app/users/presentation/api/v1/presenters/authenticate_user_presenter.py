from typing import override

from fastapi import status
from fastapi.responses import JSONResponse

from app.shared.presentation.api.errors import error_response
from app.users.application.session import Session
from app.users.application.use_cases.authenticate_user import (
    AuthenticateUserOutputPort,
)
from app.users.presentation.api.v1.schemas.authenticate_user import (
    SessionResponse,
)


class AuthenticateUserHttpPresenter(AuthenticateUserOutputPort):
    def __init__(self) -> None:
        self._response: JSONResponse | None = None

    def response(self) -> JSONResponse:
        if self._response is None:
            raise RuntimeError("O caso de uso terminou sem apresentar um resultado.")
        return self._response

    @override
    def present_authenticated(self, session: Session) -> None:
        corpo = SessionResponse.from_session(session).model_dump()
        self._response = JSONResponse(
            corpo,
            status_code=status.HTTP_200_OK,
            headers={"Cache-Control": "no-store"},
        )

    @override
    def present_invalid_credentials(self) -> None:
        self._response = error_response(
            status.HTTP_401_UNAUTHORIZED,
            "invalid_credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

    @override
    def present_too_many_attempts(self, retry_after: int) -> None:
        self._response = error_response(
            status.HTTP_429_TOO_MANY_REQUESTS,
            "too_many_attempts",
            headers={"Retry-After": str(retry_after)},
        )
