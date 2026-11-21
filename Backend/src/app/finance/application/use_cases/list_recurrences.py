from dataclasses import dataclass
from datetime import date
from typing import Protocol, override

from app.finance.application.dtos.recurrences import (
    ListRecurrencesInput,
    RecurrenceOutput,
)
from app.finance.application.ports.unit_of_work import UnitOfWork
from app.finance.domain.services.next_occurrence import next_occurrence
from app.finance.domain.services.recurrence_rules import RecurrenceRules
from app.finance.domain.value_objects.owner_id import OwnerId
from app.shared.domain.clock import Clock


class ListRecurrencesInputPort(Protocol):
    async def execute(self, data: ListRecurrencesInput) -> None: ...


class ListRecurrencesOutputPort(Protocol):
    def present_listed(self, recurrences: list[RecurrenceOutput]) -> None: ...


@dataclass(frozen=True, slots=True)
class ListRecurrencesInteractor(ListRecurrencesInputPort):
    uow: UnitOfWork
    rules: RecurrenceRules
    clock: Clock
    presenter: ListRecurrencesOutputPort

    @override
    async def execute(self, data: ListRecurrencesInput) -> None:
        async with self.uow:
            recorrencias = await self.uow.recurrences.list_by_owner(
                OwnerId(data.owner_id)
            )
        hoje = self.clock.today()
        itens = [
            RecurrenceOutput.from_recurrence(
                r,
                next_occurrence(r.schedule, r.starts_on, r.ends_on, hoje, self.rules),
            )
            for r in recorrencias
        ]
        self.presenter.present_listed(sorted(itens, key=_ordem))


def _ordem(item: RecurrenceOutput) -> tuple[bool, date, str]:
    sem_data = item.next_occurrence_on is None
    data = (
        date.max
        if item.next_occurrence_on is None
        else date.fromisoformat(item.next_occurrence_on)
    )
    return sem_data, data, item.description.lower()
