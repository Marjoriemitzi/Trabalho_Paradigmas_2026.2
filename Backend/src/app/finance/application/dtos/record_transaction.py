import uuid
from dataclasses import dataclass
from datetime import date
from typing import Self

from app.finance.application.dtos.transaction_warning import TransactionWarning
from app.finance.domain.entities.transaction import Transaction


@dataclass(frozen=True, slots=True)
class RecordTransactionInput:
    owner_id: uuid.UUID
    account_id: uuid.UUID
    kind: str
    amount_cents: int
    description: str
    occurred_on: date
    category: str | None = None


@dataclass(frozen=True, slots=True)
class RecordedTransaction:
    id: str
    account_id: str
    kind: str
    amount_cents: int
    description: str
    category: str
    occurred_on: str
    warnings: tuple[TransactionWarning, ...] = ()

    @classmethod
    def from_transaction(
        cls, transaction: Transaction, warnings: tuple[TransactionWarning, ...] = ()
    ) -> Self:
        return cls(
            id=str(transaction.id.value),
            account_id=str(transaction.account.value),
            kind=transaction.kind.value,
            amount_cents=transaction.amount.cents,
            description=transaction.description.text,
            category=transaction.category.name,
            occurred_on=transaction.occurred_on.isoformat(),
            warnings=warnings,
        )
