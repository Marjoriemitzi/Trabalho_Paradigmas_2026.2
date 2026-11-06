from fastapi import Request

from app.users.presentation.api.v1.controllers.register_user_controller import (
    RegisterUserController,
    RegisterUserFactory,
)


def get_register_user_controller(request: Request) -> RegisterUserController:
    factory: RegisterUserFactory = request.app.state.register_user
    return RegisterUserController(factory)
