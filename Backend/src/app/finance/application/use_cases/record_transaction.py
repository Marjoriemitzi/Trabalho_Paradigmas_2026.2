from dataclasses import dataclass
from typing import Protocol

from app.finance.application.dtos.record_transaction import (
    RecordedTransaction,
    RecordTransactionInput,
)
from app.finance.application.fields import InvalidFieldError
from app.finance.application.ports.transaction_check import TransactionCheck
from app.finance.application.ports.unit_of_work import UnitOfWork
from app.finance.application.transaction_fields import (
    read_transaction_fields,
    reference_problem,
    run_checks,
)
from app.finance.domain.entities.transaction import Transaction
from app.finance.domain.services.categorizer import Categorizer
from app.finance.domain.value_objects.owner_id import OwnerId


class RecordTransactionInputPort(Protocol):
    async def execute(self, data: RecordTransactionInput) -> None: ...


class RecordTransactionOutputPort(Protocol):
    def present_recorded(self, transaction: RecordedTransaction) -> None: ...

    def present_invalid(self, field: str, problem: str) -> None: ...


@dataclass(frozen=True, slots=True)
class RecordTransactionInteractor(RecordTransactionInputPort):
    uow: UnitOfWork
    categorizer: Categorizer
    presenter: RecordTransactionOutputPort
    checks: tuple[TransactionCheck, ...] = ()

    async def execute(self, data: RecordTransactionInput) -> None:
        try:
            campos = read_transaction_fields(data, self.categorizer)
        except InvalidFieldError as error:
            self.presenter.present_invalid(error.field, error.problem)
            return

        owner = OwnerId(data.owner_id)
        async with self.uow:
            problema = await reference_problem(self.uow, owner, campos)
            if problema is not None:
                self.presenter.present_invalid(problema.field, problema.problem)
                return
            transaction = Transaction.record(
                owner=owner,
                account=campos.account,
                kind=campos.kind,
                amount=campos.amount,
                description=campos.description,
                category=campos.category,
                occurred_on=campos.occurred_on,
            )
            await self.uow.transactions.add(transaction)
            avisos = await run_checks(self.checks, transaction, self.uow)
            await self.uow.commit()

        self.presenter.present_recorded(
            RecordedTransaction.from_transaction(transaction, avisos)
        )
