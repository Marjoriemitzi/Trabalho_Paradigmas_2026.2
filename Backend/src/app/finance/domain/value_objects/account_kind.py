from enum import StrEnum
from typing import Self

from app.finance.domain.exceptions import InvalidValueError


class AccountKind(StrEnum):
    WALLET = "wallet"
    CHECKING = "checking"
    CREDIT_CARD = "credit_card"

    @classmethod
    def parse(cls, value: str) -> Self:
        try:
            return cls(value)
        except ValueError:
            raise InvalidValueError("unknown") from None
