from dataclasses import dataclass
from typing import Protocol, override

from app.finance.application.dtos.recurrences import (
    CreateRecurrenceInput,
    RecurrenceOutput,
)
from app.finance.application.fields import InvalidFieldError
from app.finance.application.ports.unit_of_work import UnitOfWork
from app.finance.application.recurrence_fields import (
    read_recurrence_fields,
    recurrence_reference_problem,
)
from app.finance.domain.entities.recurrence import Recurrence
from app.finance.domain.services.next_occurrence import next_occurrence
from app.finance.domain.services.recurrence_rules import RecurrenceRules
from app.finance.domain.value_objects.owner_id import OwnerId
from app.shared.domain.clock import Clock


class CreateRecurrenceInputPort(Protocol):
    async def execute(self, data: CreateRecurrenceInput) -> None: ...


class CreateRecurrenceOutputPort(Protocol):
    def present_created(self, recurrence: RecurrenceOutput) -> None: ...

    def present_invalid(self, field: str, problem: str) -> None: ...


@dataclass(frozen=True, slots=True)
class CreateRecurrenceInteractor(CreateRecurrenceInputPort):
    uow: UnitOfWork
    rules: RecurrenceRules
    clock: Clock
    presenter: CreateRecurrenceOutputPort

    @override
    async def execute(self, data: CreateRecurrenceInput) -> None:
        try:
            campos = read_recurrence_fields(data)
        except InvalidFieldError as error:
            self.presenter.present_invalid(error.field, error.problem)
            return

        owner = OwnerId(data.owner_id)
        async with self.uow:
            problema = await recurrence_reference_problem(self.uow, owner, campos)
            if problema is not None:
                self.presenter.present_invalid(problema.field, problema.problem)
                return
            recurrence = Recurrence.create(
                owner=owner,
                account=campos.account,
                kind=campos.kind,
                amount=campos.amount,
                description=campos.description,
                category=campos.category,
                schedule=campos.schedule,
                window=campos.window,
            )
            await self.uow.recurrences.add(recurrence)
            await self.uow.commit()

        proxima = next_occurrence(
            recurrence.schedule,
            recurrence.starts_on,
            recurrence.ends_on,
            self.clock.today(),
            self.rules,
        )
        self.presenter.present_created(
            RecurrenceOutput.from_recurrence(recurrence, proxima)
        )
