import logging
from collections.abc import Callable
from dataclasses import dataclass
from datetime import date
from typing import Protocol, override

from app.finance.application.dtos.record_transaction import RecordTransactionInput
from app.finance.application.fields import InvalidFieldError
from app.finance.application.ports.transaction_check import TransactionCheck
from app.finance.application.ports.unit_of_work import UnitOfWork
from app.finance.application.recording import record_in
from app.finance.application.transaction_fields import read_transaction_fields
from app.finance.domain.entities.recurrence import Recurrence
from app.finance.domain.exceptions import DuplicateOccurrenceError
from app.finance.domain.services.categorizer import Categorizer
from app.finance.domain.services.pending_run import pending_run
from app.finance.domain.services.recurrence_rules import RecurrenceRules

logger = logging.getLogger(__name__)


@dataclass(frozen=True, slots=True)
class RunReport:
    recurrences: int
    created: int
    skipped_days: int
    failures: int


@dataclass(frozen=True, slots=True)
class _Outcome:
    created: int = 0
    skipped_days: int = 0
    failed: bool = False


class RunDueRecurrencesInputPort(Protocol):
    async def execute(self, today: date) -> None: ...


class RunDueRecurrencesOutputPort(Protocol):
    def present_report(self, report: RunReport) -> None: ...


RunDueRecurrencesFactory = Callable[
    [RunDueRecurrencesOutputPort], RunDueRecurrencesInputPort
]


@dataclass(frozen=True, slots=True)
class RunDueRecurrencesInteractor(RunDueRecurrencesInputPort):
    """Lança as ocorrências pendentes de todas as pessoas, de forma idempotente.

    Cada recorrência roda numa Unit of Work própria, com um commit só: as transações e a
    `last_run_on` entram juntas ou nenhuma entra. A falha de uma não impede as outras.
    """

    uow_factory: Callable[[], UnitOfWork]
    categorizer: Categorizer
    checks: tuple[TransactionCheck, ...]
    rules: RecurrenceRules
    presenter: RunDueRecurrencesOutputPort

    @override
    async def execute(self, today: date) -> None:
        async with self.uow_factory() as uow:
            pendentes = await uow.recurrences.list_pending(today)

        desfechos = [await self._run_one(r, today) for r in pendentes]
        self.presenter.present_report(
            RunReport(
                recurrences=len(pendentes),
                created=sum(d.created for d in desfechos),
                skipped_days=sum(d.skipped_days for d in desfechos),
                failures=sum(1 for d in desfechos if d.failed),
            )
        )

    async def _run_one(self, pendente: Recurrence, today: date) -> _Outcome:
        try:
            return await self._launch(pendente, today)
        except DuplicateOccurrenceError:
            logger.error(
                "Recorrência %s: ocorrência já lançada por outra execução; desfeita.",
                pendente.id.value,
            )
            return _Outcome(failed=True)

    async def _launch(self, pendente: Recurrence, today: date) -> _Outcome:
        async with self.uow_factory() as uow:
            recurrence = await uow.recurrences.get(pendente.owner, pendente.id)
            if recurrence is None:
                return _Outcome()
            execucao = pending_run(recurrence, today, self.rules)
            if execucao.skipped_days > 0:
                logger.warning(
                    "Recorrência %s: %d dia(s) além do limite de recuperação foram "
                    "pulados.",
                    recurrence.id.value,
                    execucao.skipped_days,
                )
            criadas = 0
            for dia in execucao.days:
                recusa = await self._launch_day(uow, recurrence, dia)
                if recusa is not None:
                    logger.error(
                        "Recorrência %s em %s recusada: %s %s",
                        recurrence.id.value,
                        dia,
                        recusa.field,
                        recusa.problem,
                    )
                    return _Outcome(skipped_days=execucao.skipped_days, failed=True)
                criadas += 1
            if execucao.last_day is not None:
                recurrence.mark_run(execucao.last_day)
                await uow.recurrences.update(recurrence)
            await uow.commit()
        return _Outcome(created=criadas, skipped_days=execucao.skipped_days)

    async def _launch_day(
        self, uow: UnitOfWork, recurrence: Recurrence, dia: date
    ) -> InvalidFieldError | None:
        pedido = RecordTransactionInput(
            owner_id=recurrence.owner.value,
            account_id=recurrence.account.value,
            kind=recurrence.kind.value,
            amount_cents=recurrence.amount.cents,
            description=recurrence.description.text,
            occurred_on=dia,
            category=None if recurrence.category is None else recurrence.category.name,
        )
        try:
            campos = read_transaction_fields(pedido, self.categorizer)
        except InvalidFieldError as erro:
            return erro
        resultado = await record_in(
            uow, recurrence.owner, campos, self.checks, recurrence.id
        )
        for aviso in resultado.warnings:
            logger.info(
                "Recorrência %s em %s: aviso %s %s",
                recurrence.id.value,
                dia,
                aviso.code,
                dict(aviso.details),
            )
        return resultado.problem
