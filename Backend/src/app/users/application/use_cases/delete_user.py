from dataclasses import dataclass
from typing import Protocol
from pydantic import SecretStr
from app.users.application.ports.password_hasher import PasswordHasher
from app.users.application.ports.unit_of_work import UnitOfWork
from app.users.domain.value_objects.user_id import UserId


@dataclass(frozen=True, slots=True)
class DeleteUserRequest:
    user_id: str
    password: str


class DeleteUserOutputPort(Protocol):
    def present_success(self) -> None: ...
    def present_invalid_current_password(self) -> None: ...
    def present_user_not_found(self) -> None: ...


class DeleteUserInteractor:
    def __init__(
        self, uow: UnitOfWork, hasher: PasswordHasher, presenter: DeleteUserOutputPort
    ) -> None:
        self._uow = uow
        self._hasher = hasher
        self._presenter = presenter

    async def execute(self, request: DeleteUserRequest) -> None:
        try:
            user_id = UserId(request.user_id)
        except ValueError:
            self._presenter.present_user_not_found()
            return

        user = await self._uow.users.get_by_id(user_id)
        if not user:
            self._presenter.present_user_not_found()
            return

        if not self._hasher.verify(SecretStr(request.password), user.password_hash):
            self._presenter.present_invalid_current_password()
            return

        await self._uow.users.remove(user)
        await self._uow.commit()
        self._presenter.present_success()
