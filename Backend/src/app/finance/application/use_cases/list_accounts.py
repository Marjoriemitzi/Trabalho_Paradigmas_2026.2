from dataclasses import dataclass
from typing import Protocol

from app.finance.application.dtos.list_accounts import (
    AccountSummary,
    ListAccountsInput,
)
from app.finance.application.ports.unit_of_work import UnitOfWork
from app.finance.domain.value_objects.owner_id import OwnerId
from app.finance.domain.value_objects.totals import Totals
from app.finance.domain.value_objects.transfer_flows import TransferFlows


class ListAccountsInputPort(Protocol):
    async def execute(self, data: ListAccountsInput) -> None: ...


class ListAccountsOutputPort(Protocol):
    def present_accounts(self, accounts: tuple[AccountSummary, ...]) -> None: ...


@dataclass(frozen=True, slots=True)
class ListAccountsInteractor(ListAccountsInputPort):
    uow: UnitOfWork
    presenter: ListAccountsOutputPort

    async def execute(self, data: ListAccountsInput) -> None:
        owner = OwnerId(data.owner_id)
        async with self.uow:
            contas = await self.uow.accounts.list_by_owner(owner)
            totais = await self.uow.transactions.totals_by_account(owner)
            fluxos = await self.uow.transfers.flows_by_account(owner)

        self.presenter.present_accounts(
            tuple(
                AccountSummary.from_account(
                    c, totais.get(c.id, Totals()), fluxos.get(c.id, TransferFlows())
                )
                for c in contas
            )
        )
