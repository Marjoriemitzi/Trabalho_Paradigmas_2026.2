from enum import StrEnum
from typing import Self

from app.finance.domain.exceptions import InvalidValueError


class Frequency(StrEnum):
    MONTHLY = "monthly"
    WEEKLY = "weekly"

    @classmethod
    def parse(cls, value: str) -> Self:
        try:
            return cls(value)
        except ValueError:
            raise InvalidValueError("unknown") from None
