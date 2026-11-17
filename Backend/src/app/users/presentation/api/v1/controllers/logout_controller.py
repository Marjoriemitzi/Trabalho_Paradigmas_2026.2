from collections.abc import Callable

from fastapi import Response, status

from app.users.application.use_cases.logout_user import (
    LogoutUserInputPort,
    LogoutUserOutputPort,
    LogoutUserRequest,
)


class LogoutHttpPresenter(LogoutUserOutputPort):
    def __init__(self) -> None:
        self.response: Response | None = None

    def present_success(self) -> None:
        self.response = Response(status_code=status.HTTP_204_NO_CONTENT)


LogoutFactory = Callable[[LogoutUserOutputPort], LogoutUserInputPort]


class LogoutController:
    def __init__(self, factory: LogoutFactory) -> None:
        self._factory = factory

    async def handle(self, request: LogoutUserRequest) -> Response:
        presenter = LogoutHttpPresenter()
        interactor = self._factory(presenter)
        await interactor.execute(request)
        return presenter.response  # type: ignore
