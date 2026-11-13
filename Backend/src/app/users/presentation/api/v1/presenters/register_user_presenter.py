from fastapi import status
from fastapi.responses import JSONResponse

from app.shared.presentation.api.errors import error_response
from app.users.application.dtos.register_user import RegisteredUser
from app.users.application.use_cases.register_user import RegisterUserOutputPort
from app.users.presentation.api.v1.schemas.register_user import RegisteredUserResponse


class RegisterUserHttpPresenter(RegisterUserOutputPort):
    def __init__(self) -> None:
        self._response: JSONResponse | None = None

    def response(self) -> JSONResponse:
        if self._response is None:
            raise RuntimeError("O caso de uso terminou sem apresentar um resultado.")
        return self._response

    def present_registered(self, user: RegisteredUser) -> None:
        corpo = RegisteredUserResponse.from_output(user).model_dump()
        self._response = JSONResponse(corpo, status_code=status.HTTP_201_CREATED)

    def present_email_taken(self, email: str) -> None:
        self._response = error_response(status.HTTP_409_CONFLICT, "email_taken")

    def present_weak_password(self, reasons: list[str]) -> None:
        self._response = error_response(
            status.HTTP_422_UNPROCESSABLE_CONTENT, "weak_password", reasons=reasons
        )

    def present_invalid_email(self, email: str) -> None:
        self._response = error_response(
            status.HTTP_422_UNPROCESSABLE_CONTENT, "invalid_email"
        )
