from dataclasses import dataclass

from app.finance.application.ports.unit_of_work import UnitOfWork
from app.finance.application.use_cases.create_account import AccountDto
from app.finance.application.use_cases.create_account import (
    CreateAccountOutputPort as RenameAccountOutputPort,
)
from app.finance.domain.exceptions import AccountNameTakenError, InvalidAccountError
from app.finance.domain.value_objects.account_id import AccountId
from app.finance.domain.value_objects.account_name import AccountName
from app.finance.domain.value_objects.owner_id import OwnerId


@dataclass(frozen=True, slots=True)
class RenameAccountRequest:
    owner_id: str
    account_id: str
    name: str


class RenameAccountInteractor:
    def __init__(self, uow: UnitOfWork, presenter: RenameAccountOutputPort) -> None:
        self._uow = uow
        self._presenter = presenter

    async def execute(self, request: RenameAccountRequest) -> None:
        try:
            owner_id = OwnerId(request.owner_id)
            account_id = AccountId(request.account_id)
            name = AccountName(request.name)
        except InvalidAccountError as error:
            self._presenter.present_invalid_account(
                [{"field": f, "problem": p} for f, p in error.problems]
            )
            return
        except ValueError:
            self._presenter.present_account_not_found()
            return

        account = await self._uow.accounts.get(owner_id, account_id)
        if not account:
            self._presenter.present_account_not_found()
            return

        account.rename(name)
        try:
            await self._uow.accounts.update(account)
            await self._uow.commit()
            self._presenter.present_account_created(
                AccountDto(
                    id=account.id.value,
                    name=account.name.value,
                    kind=account.kind.value,
                )
            )
        except AccountNameTakenError:
            self._presenter.present_account_name_taken()
