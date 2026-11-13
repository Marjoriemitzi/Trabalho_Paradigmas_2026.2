from dataclasses import dataclass
from typing import Protocol

from app.finance.application.dtos.get_statement import (
    GetStatementInput,
    StatementOutput,
)
from app.finance.application.ports.unit_of_work import UnitOfWork
from app.finance.domain.entities.transfer import Transfer
from app.finance.domain.exceptions import InvalidValueError
from app.finance.domain.value_objects.account_id import AccountId
from app.finance.domain.value_objects.owner_id import OwnerId
from app.finance.domain.value_objects.period import Period
from app.finance.domain.value_objects.statement import Statement


class GetStatementInputPort(Protocol):
    async def execute(self, data: GetStatementInput) -> None: ...


class GetStatementOutputPort(Protocol):
    def present_statement(self, statement: StatementOutput) -> None: ...

    def present_invalid(self, field: str, problem: str) -> None: ...

    def present_account_not_found(self) -> None: ...


@dataclass(frozen=True, slots=True)
class GetStatementInteractor(GetStatementInputPort):
    uow: UnitOfWork
    presenter: GetStatementOutputPort

    async def execute(self, data: GetStatementInput) -> None:
        try:
            period = Period(data.start, data.end)
        except InvalidValueError as error:
            self.presenter.present_invalid("to", error.problem)
            return

        owner = OwnerId(data.owner_id)
        account = None if data.account_id is None else AccountId(data.account_id)
        async with self.uow:
            if account is not None:
                conta = await self.uow.accounts.get(owner, account)
                if conta is None:
                    self.presenter.present_account_not_found()
                    return
            anterior = await self.uow.transactions.totals_before(
                owner, period.start, account
            )
            lancamentos = await self.uow.transactions.list_between(
                owner, period, account
            )
            saldo_anterior = anterior.balance_cents
            transferencias: list[Transfer] = []
            if account is not None:
                fluxos = await self.uow.transfers.flows_before(
                    owner, account, period.start
                )
                saldo_anterior += fluxos.net_cents
                transferencias = await self.uow.transfers.list_between(
                    owner, account, period
                )

        statement = Statement(
            period=period,
            opening_balance_cents=saldo_anterior,
            transactions=tuple(lancamentos),
            transfers=tuple(transferencias),
            account=account,
        )
        self.presenter.present_statement(StatementOutput.from_statement(statement))
