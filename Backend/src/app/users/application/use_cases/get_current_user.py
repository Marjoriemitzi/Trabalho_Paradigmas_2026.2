from dataclasses import dataclass
from typing import Protocol

from app.users.application.dtos.get_current_user import UserProfile
from app.users.application.ports.token_verifier import AuthenticatedUser
from app.users.application.ports.unit_of_work import UnitOfWork


class GetCurrentUserInputPort(Protocol):
    async def execute(self, current: AuthenticatedUser) -> None: ...


class GetCurrentUserOutputPort(Protocol):
    def present_user(self, user: UserProfile) -> None: ...

    def present_user_not_found(self) -> None: ...


@dataclass(frozen=True, slots=True)
class GetCurrentUserInteractor(GetCurrentUserInputPort):
    uow: UnitOfWork
    presenter: GetCurrentUserOutputPort

    async def execute(self, current: AuthenticatedUser) -> None:
        async with self.uow:
            user = await self.uow.users.get_by_id(current.id)

        if user is None:
            self.presenter.present_user_not_found()
            return
        self.presenter.present_user(UserProfile.from_user(user))
