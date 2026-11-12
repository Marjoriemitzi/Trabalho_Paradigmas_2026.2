from collections.abc import Iterable
from dataclasses import dataclass
from typing import Self

from app.finance.domain.entities.transaction import Transaction
from app.finance.domain.value_objects.transaction_kind import TransactionKind


@dataclass(frozen=True, slots=True)
class Totals:
    income_cents: int = 0
    expense_cents: int = 0

    @classmethod
    def of(cls, transactions: Iterable[Transaction]) -> Self:
        entrou = saiu = 0
        for transacao in transactions:
            if transacao.kind is TransactionKind.INCOME:
                entrou += transacao.amount.cents
            else:
                saiu += transacao.amount.cents
        return cls(income_cents=entrou, expense_cents=saiu)

    @property
    def balance_cents(self) -> int:
        return self.income_cents - self.expense_cents
