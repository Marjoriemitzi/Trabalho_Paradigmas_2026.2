from dataclasses import dataclass
from datetime import date
from typing import Self

from app.finance.domain.value_objects.category import Category
from app.finance.domain.value_objects.description import Description
from app.finance.domain.value_objects.money import Money
from app.finance.domain.value_objects.owner_id import OwnerId
from app.finance.domain.value_objects.transaction_id import TransactionId
from app.finance.domain.value_objects.transaction_kind import TransactionKind


@dataclass(eq=False, slots=True)
class Transaction:
    id: TransactionId
    owner: OwnerId
    kind: TransactionKind
    amount: Money
    description: Description
    category: Category
    occurred_on: date

    @classmethod
    def record(
        cls,
        owner: OwnerId,
        kind: TransactionKind,
        amount: Money,
        description: Description,
        category: Category,
        occurred_on: date,
    ) -> Self:
        return cls(
            id=TransactionId.new(),
            owner=owner,
            kind=kind,
            amount=amount,
            description=description,
            category=category,
            occurred_on=occurred_on,
        )

    def __eq__(self, other: object) -> bool:
        return isinstance(other, Transaction) and other.id == self.id

    def __hash__(self) -> int:
        return hash(self.id)
