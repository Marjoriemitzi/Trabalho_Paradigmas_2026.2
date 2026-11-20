from fastapi import Request

from app.users.presentation.api.v1.controllers.authenticate_user_controller import (
    AuthenticateUserController,
    AuthenticateUserFactory,
)
from app.users.presentation.api.v1.controllers.change_password_controller import (
    ChangePasswordController,
    ChangePasswordFactory,
)
from app.users.presentation.api.v1.controllers.delete_user_controller import (
    DeleteUserController,
    DeleteUserFactory,
)
from app.users.presentation.api.v1.controllers.get_current_user_controller import (
    GetCurrentUserController,
    GetCurrentUserFactory,
)
from app.users.presentation.api.v1.controllers.logout_controller import (
    LogoutController,
    LogoutFactory,
)
from app.users.presentation.api.v1.controllers.refresh_session_controller import (
    RefreshSessionController,
    RefreshSessionFactory,
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


def get_change_password_controller(request: Request) -> ChangePasswordController:
    factory: ChangePasswordFactory = request.app.state.change_password
    return ChangePasswordController(factory)


def get_delete_user_controller(request: Request) -> DeleteUserController:
    factory: DeleteUserFactory = request.app.state.delete_user
    return DeleteUserController(factory)


def get_refresh_session_controller(request: Request) -> RefreshSessionController:
    factory: RefreshSessionFactory = request.app.state.refresh_session
    return RefreshSessionController(factory)


def get_logout_controller(request: Request) -> LogoutController:
    factory: LogoutFactory = request.app.state.logout
    return LogoutController(factory)
