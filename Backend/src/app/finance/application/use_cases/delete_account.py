from dataclasses import dataclass
from typing import Protocol

from app.finance.application.dtos.delete_account import DeleteAccountInput
from app.finance.application.ports.unit_of_work import UnitOfWork
from app.finance.domain.exceptions import AccountInUseError
from app.finance.domain.value_objects.account_id import AccountId
from app.finance.domain.value_objects.owner_id import OwnerId


class DeleteAccountInputPort(Protocol):
    async def execute(self, data: DeleteAccountInput) -> None: ...


class DeleteAccountOutputPort(Protocol):
    def present_deleted(self) -> None: ...

    def present_in_use(self) -> None: ...

    def present_not_found(self) -> None: ...


@dataclass(frozen=True, slots=True)
class DeleteAccountInteractor(DeleteAccountInputPort):
    uow: UnitOfWork
    presenter: DeleteAccountOutputPort

    async def execute(self, data: DeleteAccountInput) -> None:
        owner = OwnerId(data.owner_id)
        try:
            async with self.uow:
                account = await self.uow.accounts.get(owner, AccountId(data.account_id))
                if account is None:
                    self.presenter.present_not_found()
                    return
                if await self.uow.account_usage.in_use(owner, account):
                    self.presenter.present_in_use()
                    return
                await self.uow.accounts.remove(account)
                await self.uow.commit()
        except AccountInUseError:
            self.presenter.present_in_use()
            return

        self.presenter.present_deleted()
