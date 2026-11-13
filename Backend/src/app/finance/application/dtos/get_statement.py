import uuid
from dataclasses import dataclass
from datetime import date
from typing import Self

from app.finance.domain.entities.transaction import Transaction
from app.finance.domain.entities.transfer import Transfer
from app.finance.domain.value_objects.statement import Statement


@dataclass(frozen=True, slots=True)
class GetStatementInput:
    owner_id: uuid.UUID
    start: date
    end: date
    account_id: uuid.UUID | None = None


@dataclass(frozen=True, slots=True)
class StatementEntry:
    id: str
    account_id: str
    kind: str
    amount_cents: int
    description: str
    category: str
    occurred_on: str

    @classmethod
    def from_transaction(cls, transaction: Transaction) -> Self:
        return cls(
            id=str(transaction.id.value),
            account_id=str(transaction.account.value),
            kind=transaction.kind.value,
            amount_cents=transaction.amount.cents,
            description=transaction.description.text,
            category=transaction.category.name,
            occurred_on=transaction.occurred_on.isoformat(),
        )


@dataclass(frozen=True, slots=True)
class StatementTransfer:
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


@dataclass(frozen=True, slots=True)
class StatementOutput:
    start: str
    end: str
    account_id: str | None
    opening_balance_cents: int
    income_cents: int
    expense_cents: int
    closing_balance_cents: int
    transactions: tuple[StatementEntry, ...]
    transfers_in_cents: int = 0
    transfers_out_cents: int = 0
    transfers: tuple[StatementTransfer, ...] = ()

    @classmethod
    def from_statement(cls, statement: Statement) -> Self:
        account = statement.account
        return cls(
            start=statement.period.start.isoformat(),
            end=statement.period.end.isoformat(),
            account_id=None if account is None else str(account.value),
            opening_balance_cents=statement.opening_balance_cents,
            income_cents=statement.totals.income_cents,
            expense_cents=statement.totals.expense_cents,
            closing_balance_cents=statement.closing_balance_cents,
            transactions=tuple(
                StatementEntry.from_transaction(t) for t in statement.transactions
            ),
            transfers_in_cents=statement.transfer_flows.incoming_cents,
            transfers_out_cents=statement.transfer_flows.outgoing_cents,
            transfers=tuple(
                StatementTransfer.from_transfer(t) for t in statement.transfers
            ),
        )
