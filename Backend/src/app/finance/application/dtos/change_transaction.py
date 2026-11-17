import uuid
from dataclasses import dataclass
from datetime import date


@dataclass(frozen=True, slots=True)
class UpdateTransactionInput:
    owner_id: uuid.UUID
    transaction_id: uuid.UUID
    account_id: uuid.UUID
    kind: str
    amount_cents: int
    description: str
    occurred_on: date
    category: str | None = None


@dataclass(frozen=True, slots=True)
class DeleteTransactionInput:
    owner_id: uuid.UUID
    transaction_id: uuid.UUID
