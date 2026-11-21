import uuid
from datetime import date
from typing import Self

from pydantic import BaseModel, ConfigDict, StrictInt

from app.finance.application.dtos.recurrences import (
    CreateRecurrenceInput,
    RecurrenceOutput,
    UpdateRecurrenceInput,
)
from app.shared.presentation.api.schema_types import IsoDateStr, UuidStr


class RecurrenceRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    account_id: uuid.UUID
    kind: str
    amount_cents: StrictInt
    description: str
    category: str | None = None
    frequency: str
    day: StrictInt
    starts_on: date
    ends_on: date | None = None

    def to_input(self, owner_id: uuid.UUID) -> CreateRecurrenceInput:
        return CreateRecurrenceInput(
            owner_id=owner_id,
            account_id=self.account_id,
            kind=self.kind,
            amount_cents=self.amount_cents,
            description=self.description,
            category=self.category,
            frequency=self.frequency,
            day=self.day,
            starts_on=self.starts_on,
            ends_on=self.ends_on,
        )

    def to_update_input(
        self, owner_id: uuid.UUID, recurrence_id: uuid.UUID
    ) -> UpdateRecurrenceInput:
        return UpdateRecurrenceInput(
            owner_id=owner_id,
            recurrence_id=recurrence_id,
            account_id=self.account_id,
            kind=self.kind,
            amount_cents=self.amount_cents,
            description=self.description,
            category=self.category,
            frequency=self.frequency,
            day=self.day,
            starts_on=self.starts_on,
            ends_on=self.ends_on,
        )


class RecurrenceResponse(BaseModel):
    id: UuidStr
    account_id: UuidStr
    kind: str
    amount_cents: int
    description: str
    category: str | None
    frequency: str
    day: int
    starts_on: IsoDateStr
    ends_on: IsoDateStr | None
    next_occurrence_on: IsoDateStr | None
    last_run_on: IsoDateStr | None

    @classmethod
    def from_output(cls, recurrence: RecurrenceOutput) -> Self:
        return cls(
            id=recurrence.id,
            account_id=recurrence.account_id,
            kind=recurrence.kind,
            amount_cents=recurrence.amount_cents,
            description=recurrence.description,
            category=recurrence.category,
            frequency=recurrence.frequency,
            day=recurrence.day,
            starts_on=recurrence.starts_on,
            ends_on=recurrence.ends_on,
            next_occurrence_on=recurrence.next_occurrence_on,
            last_run_on=recurrence.last_run_on,
        )


class RecurrenceListResponse(BaseModel):
    recurrences: list[RecurrenceResponse]
