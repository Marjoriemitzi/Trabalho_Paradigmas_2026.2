from dataclasses import dataclass
from typing import Protocol, override

from app.finance.application.dtos.create_account import AccountOutput
from app.finance.application.dtos.rename_account import RenameAccountInput
from app.finance.application.fields import InvalidFieldError, read_field
from app.finance.application.ports.unit_of_work import UnitOfWork
from app.finance.domain.exceptions import AccountNameTakenError
from app.finance.domain.value_objects.account_id import AccountId
from app.finance.domain.value_objects.account_name import AccountName
from app.finance.domain.value_objects.owner_id import OwnerId


class RenameAccountInputPort(Protocol):
    async def execute(self, data: RenameAccountInput) -> None: ...


class RenameAccountOutputPort(Protocol):
    def present_renamed(self, account: AccountOutput) -> None: ...

    def present_invalid(self, field: str, problem: str) -> None: ...

    def present_name_taken(self, name: str) -> None: ...

    def present_not_found(self) -> None: ...


@dataclass(frozen=True, slots=True)
class RenameAccountInteractor(RenameAccountInputPort):
    uow: UnitOfWork
    presenter: RenameAccountOutputPort

    @override
    async def execute(self, data: RenameAccountInput) -> None:
        try:
            name = read_field("name", AccountName, data.name)
        except InvalidFieldError as error:
            self.presenter.present_invalid(error.field, error.problem)
            return

        try:
            async with self.uow:
                account = await self.uow.accounts.get(
                    OwnerId(data.owner_id), AccountId(data.account_id)
                )
                if account is None:
                    self.presenter.present_not_found()
                    return
                account.rename(name)
                await self.uow.accounts.update(account)
                await self.uow.commit()
        except AccountNameTakenError:
            self.presenter.present_name_taken(name.text)
            return

        self.presenter.present_renamed(AccountOutput.from_account(account))
