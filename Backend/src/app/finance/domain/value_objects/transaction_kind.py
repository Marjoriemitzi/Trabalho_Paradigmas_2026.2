from enum import StrEnum
from typing import Self

from app.finance.domain.exceptions import InvalidValueError


class TransactionKind(StrEnum):
    INCOME = "income"
    EXPENSE = "expense"

    @classmethod
    def parse(cls, value: str) -> Self:
        try:
            return cls(value)
        except ValueError:
            raise InvalidValueError("unknown") from None
