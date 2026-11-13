import uuid
from dataclasses import dataclass
from datetime import date
from typing import Self

from app.finance.domain.entities.transfer import Transfer


@dataclass(frozen=True, slots=True)
class CreateTransferInput:
    owner_id: uuid.UUID
    from_account_id: uuid.UUID
    to_account_id: uuid.UUID
    amount_cents: int
    description: str
    occurred_on: date


@dataclass(frozen=True, slots=True)
class DeleteTransferInput:
    owner_id: uuid.UUID
    transfer_id: uuid.UUID


@dataclass(frozen=True, slots=True)
class TransferOutput:
    id: str
    from_account_id: str
    to_account_id: str
    amount_cents: int
    description: str
    occurred_on: str

    @classmethod
    def from_transfer(cls, transfer: Transfer) -> Self:
        return cls(
            id=str(transfer.id.value),
            from_account_id=str(transfer.source.value),
            to_account_id=str(transfer.destination.value),
            amount_cents=transfer.amount.cents,
            description=transfer.description.text,
            occurred_on=transfer.occurred_on.isoformat(),
        )
