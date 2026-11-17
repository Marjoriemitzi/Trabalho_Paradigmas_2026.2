from dataclasses import dataclass
from typing import Protocol

from pydantic import SecretStr

from app.users.application.ports.password_hasher import PasswordHasher
from app.users.application.ports.unit_of_work import UnitOfWork
from app.users.domain.services.password_policy import PasswordPolicy, WeakPasswordError
from app.users.domain.value_objects.password import Password
from app.users.domain.value_objects.user_id import UserId


@dataclass(frozen=True, slots=True)
class ChangePasswordRequest:
    user_id: str
    current_password: str
    new_password: str


class ChangePasswordOutputPort(Protocol):
    def present_success(self) -> None: ...
    def present_invalid_current_password(self) -> None: ...
    def present_weak_password(self, reasons: list[str]) -> None: ...
    def present_user_not_found(self) -> None: ...


class ChangePasswordInteractor:
    def __init__(
        self,
        uow: UnitOfWork,
        hasher: PasswordHasher,
        policy: PasswordPolicy,
        presenter: ChangePasswordOutputPort,
    ) -> None:
        self._uow = uow
        self._hasher = hasher
        self._policy = policy
        self._presenter = presenter

    async def execute(self, request: ChangePasswordRequest) -> None:
        try:
            user_id = UserId(request.user_id)
        except ValueError:
            self._presenter.present_user_not_found()
            return

        user = await self._uow.users.get_by_id(user_id)
        if not user:
            self._presenter.present_user_not_found()
            return

        if not self._hasher.verify(
            SecretStr(request.current_password), user.password_hash
        ):
            self._presenter.present_invalid_current_password()
            return

        try:
            self._policy.check(Password(request.new_password))
        except WeakPasswordError as error:
            self._presenter.present_weak_password(error.reasons)
            return

        new_hash = self._hasher.hash(SecretStr(request.new_password))
        user.change_password(new_hash)

        await self._uow.users.update_password(user)
        await self._uow.commit()
        self._presenter.present_success()
