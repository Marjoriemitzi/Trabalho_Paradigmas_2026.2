import uuid
from datetime import date
from typing import Self

from pydantic import BaseModel, ConfigDict, StrictInt

from app.finance.application.dtos.change_transaction import UpdateTransactionInput
from app.finance.application.dtos.record_transaction import (
    RecordedTransaction,
    RecordTransactionInput,
)
from app.finance.application.dtos.transaction_warning import TransactionWarning


class RecordTransactionRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    account_id: uuid.UUID
    kind: str
    amount_cents: StrictInt
    description: str
    occurred_on: date
    category: str | None = None

    def to_input(self, owner_id: uuid.UUID) -> RecordTransactionInput:
        return RecordTransactionInput(
            owner_id=owner_id,
            account_id=self.account_id,
            kind=self.kind,
            amount_cents=self.amount_cents,
            description=self.description,
            occurred_on=self.occurred_on,
            category=self.category,
        )


class UpdateTransactionRequest(RecordTransactionRequest):
    def to_update_input(
        self, owner_id: uuid.UUID, transaction_id: uuid.UUID
    ) -> UpdateTransactionInput:
        return UpdateTransactionInput(
            owner_id=owner_id,
            transaction_id=transaction_id,
            account_id=self.account_id,
            kind=self.kind,
            amount_cents=self.amount_cents,
            description=self.description,
            occurred_on=self.occurred_on,
            category=self.category,
        )


class TransactionWarningResponse(BaseModel):
    code: str
    details: dict[str, str | int]

    @classmethod
    def from_warning(cls, warning: TransactionWarning) -> Self:
        return cls(code=warning.code, details=dict(warning.details))


class RecordedTransactionResponse(BaseModel):
    id: str
    account_id: str
    kind: str
    amount_cents: int
    description: str
    category: str
    occurred_on: str
    warnings: list[TransactionWarningResponse]

    @classmethod
    def from_output(cls, transaction: RecordedTransaction) -> Self:
        return cls(
            id=transaction.id,
            account_id=transaction.account_id,
            kind=transaction.kind,
            amount_cents=transaction.amount_cents,
            description=transaction.description,
            category=transaction.category,
            occurred_on=transaction.occurred_on,
            warnings=[
                TransactionWarningResponse.from_warning(w) for w in transaction.warnings
            ],
        )
