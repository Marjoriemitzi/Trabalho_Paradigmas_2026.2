import uuid
from dataclasses import dataclass
from datetime import date
from typing import Self

from app.finance.domain.entities.recurrence import Recurrence


@dataclass(frozen=True, slots=True)
class CreateRecurrenceInput:
    owner_id: uuid.UUID
    account_id: uuid.UUID
    kind: str
    amount_cents: int
    description: str
    category: str | None
    frequency: str
    day: int
    starts_on: date
    ends_on: date | None


@dataclass(frozen=True, slots=True)
class UpdateRecurrenceInput:
    owner_id: uuid.UUID
    recurrence_id: uuid.UUID
    account_id: uuid.UUID
    kind: str
    amount_cents: int
    description: str
    category: str | None
    frequency: str
    day: int
    starts_on: date
    ends_on: date | None


@dataclass(frozen=True, slots=True)
class DeleteRecurrenceInput:
    owner_id: uuid.UUID
    recurrence_id: uuid.UUID


@dataclass(frozen=True, slots=True)
class ListRecurrencesInput:
    owner_id: uuid.UUID


@dataclass(frozen=True, slots=True)
class RecurrenceOutput:
    id: str
    account_id: str
    kind: str
    amount_cents: int
    description: str
    category: str | None
    frequency: str
    day: int
    starts_on: str
    ends_on: str | None
    next_occurrence_on: str | None

    @classmethod
    def from_recurrence(
        cls, recurrence: Recurrence, next_occurrence_on: date | None
    ) -> Self:
        return cls(
            id=str(recurrence.id.value),
            account_id=str(recurrence.account.value),
            kind=recurrence.kind.value,
            amount_cents=recurrence.amount.cents,
            description=recurrence.description.text,
            category=None if recurrence.category is None else recurrence.category.name,
            frequency=recurrence.schedule.frequency.value,
            day=recurrence.schedule.day,
            starts_on=recurrence.starts_on.isoformat(),
            ends_on=None
            if recurrence.ends_on is None
            else recurrence.ends_on.isoformat(),
            next_occurrence_on=(
                None if next_occurrence_on is None else next_occurrence_on.isoformat()
            ),
        )
