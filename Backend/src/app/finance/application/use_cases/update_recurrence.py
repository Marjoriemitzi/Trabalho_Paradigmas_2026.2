from dataclasses import dataclass
from typing import Protocol, override

from app.finance.application.dtos.recurrences import (
    RecurrenceOutput,
    UpdateRecurrenceInput,
)
from app.finance.application.fields import InvalidFieldError
from app.finance.application.ports.unit_of_work import UnitOfWork
from app.finance.application.recurrence_fields import (
    read_recurrence_fields,
    recurrence_reference_problem,
)
from app.finance.domain.services.next_occurrence import next_occurrence
from app.finance.domain.services.recurrence_rules import RecurrenceRules
from app.finance.domain.value_objects.owner_id import OwnerId
from app.finance.domain.value_objects.recurrence_id import RecurrenceId
from app.shared.domain.clock import Clock


class UpdateRecurrenceInputPort(Protocol):
    async def execute(self, data: UpdateRecurrenceInput) -> None: ...


class UpdateRecurrenceOutputPort(Protocol):
    def present_updated(self, recurrence: RecurrenceOutput) -> None: ...

    def present_invalid(self, field: str, problem: str) -> None: ...

    def present_not_found(self) -> None: ...


@dataclass(frozen=True, slots=True)
class UpdateRecurrenceInteractor(UpdateRecurrenceInputPort):
    uow: UnitOfWork
    rules: RecurrenceRules
    clock: Clock
    presenter: UpdateRecurrenceOutputPort

    @override
    async def execute(self, data: UpdateRecurrenceInput) -> None:
        try:
            campos = read_recurrence_fields(data)
        except InvalidFieldError as error:
            self.presenter.present_invalid(error.field, error.problem)
            return

        owner = OwnerId(data.owner_id)
        async with self.uow:
            recurrence = await self.uow.recurrences.get(
                owner, RecurrenceId(data.recurrence_id)
            )
            if recurrence is None:
                self.presenter.present_not_found()
                return
            problema = await recurrence_reference_problem(self.uow, owner, campos)
            if problema is not None:
                self.presenter.present_invalid(problema.field, problema.problem)
                return
            recurrence.revise(
                account=campos.account,
                kind=campos.kind,
                amount=campos.amount,
                description=campos.description,
                category=campos.category,
                schedule=campos.schedule,
                window=campos.window,
            )
            await self.uow.recurrences.update(recurrence)
            await self.uow.commit()

        proxima = next_occurrence(
            recurrence.schedule,
            recurrence.starts_on,
            recurrence.ends_on,
            self.clock.today(),
            self.rules,
        )
        self.presenter.present_updated(
            RecurrenceOutput.from_recurrence(recurrence, proxima)
        )
