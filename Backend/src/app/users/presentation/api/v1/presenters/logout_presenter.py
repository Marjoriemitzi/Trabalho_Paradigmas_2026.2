from typing import override

from fastapi import Response, status

from app.users.application.use_cases.logout import LogoutOutputPort


class LogoutHttpPresenter(LogoutOutputPort):
    def __init__(self) -> None:
        self._response: Response | None = None

    def response(self) -> Response:
        if self._response is None:
            raise RuntimeError("O caso de uso terminou sem apresentar um resultado.")
        return self._response

    @override
    def present_logged_out(self) -> None:
        self._response = Response(status_code=status.HTTP_204_NO_CONTENT)
