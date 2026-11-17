from typing import Self

from pydantic import BaseModel, Field

from app.finance.application.dtos.get_statement import (
    StatementEntry,
    StatementOutput,
    StatementTransfer,
)


class StatementEntryResponse(BaseModel):
    id: str
    account_id: str
    kind: str
    amount_cents: int
    description: str
    category: str
    occurred_on: str

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
        )


class StatementTransferResponse(BaseModel):
    id: str
    from_account_id: str
    to_account_id: str
    amount_cents: int
    description: str
    occurred_on: str

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
    start: str = Field(serialization_alias="from")
    end: str = Field(serialization_alias="to")
    account_id: str | None = Field(
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
