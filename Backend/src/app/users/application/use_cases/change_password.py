from collections.abc import Sequence
from dataclasses import dataclass
from typing import Protocol, override

from app.users.application.dtos.change_password import ChangePasswordInput
from app.users.application.ports.password_hasher import PasswordHasher
from app.users.application.ports.unit_of_work import UnitOfWork
from app.users.domain.exceptions import WeakPasswordError
from app.users.domain.services.password_policy import PasswordPolicy
from app.users.domain.value_objects.password import RawPassword


class ChangePasswordInputPort(Protocol):
    async def execute(self, data: ChangePasswordInput) -> None: ...


class ChangePasswordOutputPort(Protocol):
    def present_changed(self) -> None: ...

    def present_invalid_current_password(self) -> None: ...

    def present_weak_password(self, reasons: Sequence[str]) -> None: ...

    def present_user_not_found(self) -> None: ...


@dataclass(frozen=True, slots=True)
class ChangePasswordInteractor(ChangePasswordInputPort):
    uow: UnitOfWork
    hasher: PasswordHasher
    policy: PasswordPolicy
    presenter: ChangePasswordOutputPort

    @override
    async def execute(self, data: ChangePasswordInput) -> None:
        async with self.uow:
            user = await self.uow.users.get_by_id(data.user_id)
            if user is None:
                self.presenter.present_user_not_found()
                return

            if (
                not data.current_password
                or "\x00" in data.current_password
                or not await self.hasher.verify(
                    RawPassword(data.current_password), user.password_hash
                )
            ):
                self.presenter.present_invalid_current_password()
                return

            try:
                self.policy.check(data.new_password)
            except WeakPasswordError as error:
                self.presenter.present_weak_password(error.reasons)
                return

            user.change_password(await self.hasher.hash(RawPassword(data.new_password)))
            await self.uow.users.update_password(user)
            await self.uow.commit()

        self.presenter.present_changed()
