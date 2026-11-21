from dataclasses import dataclass

from app.finance.application.dtos.transaction_warning import TransactionWarning
from app.finance.application.fields import InvalidFieldError
from app.finance.application.ports.transaction_check import TransactionCheck
from app.finance.application.ports.unit_of_work import UnitOfWork
from app.finance.application.transaction_fields import (
    TransactionFields,
    reference_problem,
    run_checks,
)
from app.finance.domain.entities.transaction import Transaction
from app.finance.domain.value_objects.owner_id import OwnerId
from app.finance.domain.value_objects.recurrence_id import RecurrenceId


@dataclass(frozen=True, slots=True)
class RecordResult:
    """Ou a transação gravada (com os avisos), ou o problema que a recusou."""

    transaction: Transaction | None
    warnings: tuple[TransactionWarning, ...]
    problem: InvalidFieldError | None


async def record_in(
    uow: UnitOfWork,
    owner: OwnerId,
    fields: TransactionFields,
    checks: tuple[TransactionCheck, ...],
    recurrence: RecurrenceId | None = None,
) -> RecordResult:
    """O miolo do lançamento, numa Unit of Work já aberta. Quem chama dá o commit.

    É o mesmo fluxo para o lançamento feito à mão e para o gerado por uma recorrência.
    """
    problema = await reference_problem(uow, owner, fields)
    if problema is not None:
        return RecordResult(transaction=None, warnings=(), problem=problema)
    transaction = Transaction.record(
        owner=owner,
        account=fields.account,
        kind=fields.kind,
        amount=fields.amount,
        description=fields.description,
        category=fields.category,
        occurred_on=fields.occurred_on,
        recurrence=recurrence,
    )
    await uow.transactions.add(transaction)
    avisos = await run_checks(checks, transaction, uow)
    return RecordResult(transaction=transaction, warnings=avisos, problem=None)
