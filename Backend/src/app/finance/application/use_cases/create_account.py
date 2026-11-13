from dataclasses import dataclass
from typing import Protocol

from app.finance.application.dtos.create_account import (
    AccountOutput,
    CreateAccountInput,
)
from app.finance.application.fields import InvalidFieldError, read_field
from app.finance.application.ports.unit_of_work import UnitOfWork
from app.finance.domain.entities.account import Account
from app.finance.domain.exceptions import AccountNameTakenError
from app.finance.domain.value_objects.account_kind import AccountKind
from app.finance.domain.value_objects.account_name import AccountName
from app.finance.domain.value_objects.owner_id import OwnerId


class CreateAccountInputPort(Protocol):
    async def execute(self, data: CreateAccountInput) -> None: ...


class CreateAccountOutputPort(Protocol):
    def present_created(self, account: AccountOutput) -> None: ...

    def present_invalid(self, field: str, problem: str) -> None: ...

    def present_name_taken(self, name: str) -> None: ...


@dataclass(frozen=True, slots=True)
class CreateAccountInteractor(CreateAccountInputPort):
    uow: UnitOfWork
    presenter: CreateAccountOutputPort

    async def execute(self, data: CreateAccountInput) -> None:
        try:
            name = read_field("name", AccountName, data.name)
            kind = read_field("kind", AccountKind.parse, data.kind)
        except InvalidFieldError as error:
            self.presenter.present_invalid(error.field, error.problem)
            return

        account = Account.open(OwnerId(data.owner_id), name, kind)
        try:
            async with self.uow:
                await self.uow.accounts.add(account)
                await self.uow.commit()
        except AccountNameTakenError:
            self.presenter.present_name_taken(name.text)
            return

        self.presenter.present_created(AccountOutput.from_account(account))
