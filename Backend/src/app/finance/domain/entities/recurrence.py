from dataclasses import dataclass
from datetime import date
from typing import Self, override

from app.finance.domain.value_objects.account_id import AccountId
from app.finance.domain.value_objects.active_range import ActiveRange
from app.finance.domain.value_objects.category import Category
from app.finance.domain.value_objects.description import Description
from app.finance.domain.value_objects.money import Money
from app.finance.domain.value_objects.owner_id import OwnerId
from app.finance.domain.value_objects.recurrence_id import RecurrenceId
from app.finance.domain.value_objects.schedule import Schedule
from app.finance.domain.value_objects.transaction_kind import TransactionKind


@dataclass(eq=False, slots=True)
class Recurrence:
    id: RecurrenceId
    owner: OwnerId
    account: AccountId
    kind: TransactionKind
    amount: Money
    description: Description
    category: Category | None
    schedule: Schedule
    window: ActiveRange
    last_run_on: date | None = None

    @property
    def starts_on(self) -> date:
        return self.window.starts_on

    @property
    def ends_on(self) -> date | None:
        return self.window.ends_on

    @classmethod
    def create(
        cls,
        owner: OwnerId,
        account: AccountId,
        kind: TransactionKind,
        amount: Money,
        description: Description,
        category: Category | None,
        schedule: Schedule,
        window: ActiveRange,
    ) -> Self:
        return cls(
            id=RecurrenceId.new(),
            owner=owner,
            account=account,
            kind=kind,
            amount=amount,
            description=description,
            category=category,
            schedule=schedule,
            window=window,
        )

    def revise(
        self,
        account: AccountId,
        kind: TransactionKind,
        amount: Money,
        description: Description,
        category: Category | None,
        schedule: Schedule,
        window: ActiveRange,
    ) -> None:
        self.account = account
        self.kind = kind
        self.amount = amount
        self.description = description
        self.category = category
        self.schedule = schedule
        self.window = window

    def mark_run(self, day: date) -> None:
        self.last_run_on = day

    @override
    def __eq__(self, other: object) -> bool:
        return isinstance(other, Recurrence) and other.id == self.id

    @override
    def __hash__(self) -> int:
        return hash(self.id)
