from fastapi import status
from fastapi.responses import JSONResponse

from app.shared.presentation.api.errors import error_response
from app.users.application.session import Session
from app.users.application.use_cases.refresh_session import RefreshSessionOutputPort
from app.users.presentation.api.v1.schemas.authenticate_user import SessionResponse


class RefreshSessionHttpPresenter(RefreshSessionOutputPort):
    def __init__(self) -> None:
        self._response: JSONResponse | None = None

    def response(self) -> JSONResponse:
        if self._response is None:
            raise RuntimeError("O caso de uso terminou sem apresentar um resultado.")
        return self._response

    def present_refreshed(self, session: Session) -> None:
        corpo = SessionResponse.from_session(session).model_dump()
        self._response = JSONResponse(
            corpo,
            status_code=status.HTTP_200_OK,
            headers={"Cache-Control": "no-store"},
        )

    def present_invalid_refresh_token(self) -> None:
        self._response = error_response(
            status.HTTP_401_UNAUTHORIZED, "invalid_refresh_token"
        )
