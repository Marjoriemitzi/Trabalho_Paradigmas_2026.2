from dataclasses import dataclass
from typing import Protocol

from app.users.application.dtos.delete_user import DeleteUserInput
from app.users.application.ports.password_hasher import PasswordHasher
from app.users.application.ports.unit_of_work import UnitOfWork
from app.users.domain.value_objects.password import RawPassword


class DeleteUserInputPort(Protocol):
    async def execute(self, data: DeleteUserInput) -> None: ...


class DeleteUserOutputPort(Protocol):
    def present_deleted(self) -> None: ...

    def present_invalid_current_password(self) -> None: ...

    def present_user_not_found(self) -> None: ...


@dataclass(frozen=True, slots=True)
class DeleteUserInteractor(DeleteUserInputPort):
    uow: UnitOfWork
    hasher: PasswordHasher
    presenter: DeleteUserOutputPort

    async def execute(self, data: DeleteUserInput) -> None:
        async with self.uow:
            user = await self.uow.users.get_by_id(data.user_id)
            if user is None:
                self.presenter.present_user_not_found()
                return

            if not data.password or not await self.hasher.verify(
                RawPassword(data.password), user.password_hash
            ):
                self.presenter.present_invalid_current_password()
                return

            await self.uow.users.remove(user)
            await self.uow.commit()

        self.presenter.present_deleted()
