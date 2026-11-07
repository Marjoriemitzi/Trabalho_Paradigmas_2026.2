from fastapi import status
from fastapi.responses import JSONResponse

from app.users.application.dtos.get_current_user import UserProfile
from app.users.application.use_cases.get_current_user import (
    GetCurrentUserOutputPort,
)
from app.users.presentation.api.v1.schemas.get_current_user import (
    UserProfileResponse,
)
from app.users.presentation.api.v1.security import invalid_token


class GetCurrentUserHttpPresenter(GetCurrentUserOutputPort):
    def __init__(self) -> None:
        self._response: JSONResponse | None = None

    def response(self) -> JSONResponse:
        if self._response is None:
            raise RuntimeError("O caso de uso terminou sem apresentar um resultado.")
        return self._response

    def present_user(self, user: UserProfile) -> None:
        corpo = UserProfileResponse.from_profile(user).model_dump()
        self._response = JSONResponse(corpo, status_code=status.HTTP_200_OK)

    def present_user_not_found(self) -> None:
        raise invalid_token()
