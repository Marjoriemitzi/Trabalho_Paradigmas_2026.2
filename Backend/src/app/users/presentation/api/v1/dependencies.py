from typing import TYPE_CHECKING

from fastapi import Request

if TYPE_CHECKING:
    from app.users.presentation.api.v1.controllers.change_password_controller import (
        ChangePasswordController,
    )

from app.users.presentation.api.v1.controllers.authenticate_user_controller import (
    AuthenticateUserController,
    AuthenticateUserFactory,
)
from app.users.presentation.api.v1.controllers.get_current_user_controller import (
    GetCurrentUserController,
    GetCurrentUserFactory,
)
from app.users.presentation.api.v1.controllers.register_user_controller import (
    RegisterUserController,
    RegisterUserFactory,
)


def get_register_user_controller(request: Request) -> RegisterUserController:
    factory: RegisterUserFactory = request.app.state.register_user
    return RegisterUserController(factory)


def get_authenticate_user_controller(request: Request) -> AuthenticateUserController:
    factory: AuthenticateUserFactory = request.app.state.authenticate_user
    return AuthenticateUserController(factory)


def get_current_user_controller(request: Request) -> GetCurrentUserController:
    factory: GetCurrentUserFactory = request.app.state.get_current_user
    return GetCurrentUserController(factory)


def get_change_password_controller(request: Request) -> "ChangePasswordController":
    return request.app.state.change_password_factory()
