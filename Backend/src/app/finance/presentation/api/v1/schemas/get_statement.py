from typing import Self

from pydantic import BaseModel, Field

from app.finance.application.dtos.get_statement import (
    StatementEntry,
    StatementOutput,
    StatementTransfer,
)
from app.shared.presentation.api.schema_types import IsoDateStr, UuidStr


class StatementEntryResponse(BaseModel):
    id: UuidStr
    account_id: UuidStr
    kind: str
    amount_cents: int
    description: str
    category: str
    occurred_on: IsoDateStr
    recurrence_id: UuidStr | None

    @classmethod
    def from_entry(cls, entry: StatementEntry) -> Self:
        return cls(
            id=entry.id,
            account_id=entry.account_id,
            kind=entry.kind,
            amount_cents=entry.amount_cents,
            description=entry.description,
            category=entry.category,
            occurred_on=entry.occurred_on,
            recurrence_id=entry.recurrence_id,
        )


class StatementTransferResponse(BaseModel):
    id: UuidStr
    from_account_id: UuidStr
    to_account_id: UuidStr
    amount_cents: int
    description: str
    occurred_on: IsoDateStr

    @classmethod
    def from_transfer(cls, transfer: StatementTransfer) -> Self:
        return cls(
            id=transfer.id,
            from_account_id=transfer.from_account_id,
            to_account_id=transfer.to_account_id,
            amount_cents=transfer.amount_cents,
            description=transfer.description,
            occurred_on=transfer.occurred_on,
        )


class StatementResponse(BaseModel):
    start: IsoDateStr = Field(serialization_alias="from")
    end: IsoDateStr = Field(serialization_alias="to")
    account_id: UuidStr | None = Field(
        description="A conta do extrato; null quando junta todas as contas"
    )
    opening_balance_cents: int
    income_cents: int
    expense_cents: int
    closing_balance_cents: int
    transactions: list[StatementEntryResponse]
    transfers_in_cents: int
    transfers_out_cents: int
    transfers: list[StatementTransferResponse] = Field(
        description="Só no extrato de uma conta; vazio no de todas as contas"
    )

    @classmethod
    def from_output(cls, statement: StatementOutput) -> Self:
        return cls(
            start=statement.start,
            end=statement.end,
            account_id=statement.account_id,
            opening_balance_cents=statement.opening_balance_cents,
            income_cents=statement.income_cents,
            expense_cents=statement.expense_cents,
            closing_balance_cents=statement.closing_balance_cents,
            transactions=[
                StatementEntryResponse.from_entry(e) for e in statement.transactions
            ],
            transfers_in_cents=statement.transfers_in_cents,
            transfers_out_cents=statement.transfers_out_cents,
            transfers=[
                StatementTransferResponse.from_transfer(t) for t in statement.transfers
            ],
        )
