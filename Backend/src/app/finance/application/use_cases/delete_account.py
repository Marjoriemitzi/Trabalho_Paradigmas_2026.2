from dataclasses import dataclass
from typing import Protocol
from app.finance.application.ports.unit_of_work import UnitOfWork
from app.finance.domain.exceptions import AccountInUseError
from app.finance.domain.value_objects.account_id import AccountId
from app.finance.domain.value_objects.owner_id import OwnerId


@dataclass(frozen=True, slots=True)
class DeleteAccountRequest:
    owner_id: str
    account_id: str


class DeleteAccountOutputPort(Protocol):
    def present_success(self) -> None: ...
    def present_account_not_found(self) -> None: ...
    def present_account_in_use(self) -> None: ...


class DeleteAccountInteractor:
    def __init__(self, uow: UnitOfWork, presenter: DeleteAccountOutputPort) -> None:
        self._uow = uow
        self._presenter = presenter

    async def execute(self, request: DeleteAccountRequest) -> None:
        try:
            owner_id = OwnerId(request.owner_id)
            account_id = AccountId(request.account_id)
        except ValueError:
            self._presenter.present_account_not_found()
            return

        account = await self._uow.accounts.get(owner_id, account_id)
        if not account:
            self._presenter.present_account_not_found()
            return

        if await self._uow.account_usage.in_use(owner_id, account):
            self._presenter.present_account_in_use()
            return

        try:
            await self._uow.accounts.remove(account)
            await self._uow.commit()
            self._presenter.present_success()
        except AccountInUseError:
            self._presenter.present_account_in_use()
