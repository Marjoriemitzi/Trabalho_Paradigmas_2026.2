import uuid
from dataclasses import dataclass
from datetime import date
from typing import Protocol

from app.finance.application.fields import InvalidFieldError, read_field
from app.finance.application.ports.unit_of_work import UnitOfWork
from app.finance.application.transaction_fields import check_references
from app.finance.domain.exceptions import InvalidValueError
from app.finance.domain.value_objects.account_id import AccountId
from app.finance.domain.value_objects.active_range import ActiveRange
from app.finance.domain.value_objects.category import Category
from app.finance.domain.value_objects.description import Description
from app.finance.domain.value_objects.frequency import Frequency
from app.finance.domain.value_objects.money import Money
from app.finance.domain.value_objects.owner_id import OwnerId
from app.finance.domain.value_objects.schedule import Schedule
from app.finance.domain.value_objects.transaction_kind import TransactionKind


class RecurrenceFieldsInput(Protocol):
    @property
    def account_id(self) -> uuid.UUID: ...
    @property
    def kind(self) -> str: ...
    @property
    def amount_cents(self) -> int: ...
    @property
    def description(self) -> str: ...
    @property
    def category(self) -> str | None: ...
    @property
    def frequency(self) -> str: ...
    @property
    def day(self) -> int: ...
    @property
    def starts_on(self) -> date: ...
    @property
    def ends_on(self) -> date | None: ...


@dataclass(frozen=True, slots=True)
class RecurrenceFields:
    account: AccountId
    kind: TransactionKind
    amount: Money
    description: Description
    category: Category | None
    schedule: Schedule
    window: ActiveRange


def _read_schedule(frequency: str, day: int) -> Schedule:
    return Schedule(read_field("frequency", Frequency.parse, frequency), day)


def read_recurrence_fields(data: RecurrenceFieldsInput) -> RecurrenceFields:
    kind = read_field("kind", TransactionKind.parse, data.kind)
    amount = read_field("amount_cents", Money, data.amount_cents)
    description = read_field("description", Description, data.description)
    category = (
        None
        if data.category is None
        else read_field("category", Category, data.category)
    )
    try:
        schedule = _read_schedule(data.frequency, data.day)
    except InvalidValueError as error:
        raise InvalidFieldError("day", error.problem) from error
    try:
        window = ActiveRange(data.starts_on, data.ends_on)
    except InvalidValueError as error:
        raise InvalidFieldError("ends_on", error.problem) from error
    return RecurrenceFields(
        account=AccountId(data.account_id),
        kind=kind,
        amount=amount,
        description=description,
        category=category,
        schedule=schedule,
        window=window,
    )


async def recurrence_reference_problem(
    uow: UnitOfWork, owner: OwnerId, fields: RecurrenceFields
) -> InvalidFieldError | None:
    return await check_references(
        uow, owner, fields.account, fields.kind, fields.category
    )
