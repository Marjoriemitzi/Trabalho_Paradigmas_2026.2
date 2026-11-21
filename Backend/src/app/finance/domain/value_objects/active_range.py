from dataclasses import dataclass
from datetime import date

from app.finance.domain.exceptions import InvalidValueError


@dataclass(frozen=True, slots=True)
class ActiveRange:
    """De quando a quando a regra vale, com o fim opcional (os dois dias incluídos)."""

    starts_on: date
    ends_on: date | None = None

    def __post_init__(self) -> None:
        if self.ends_on is not None and self.ends_on < self.starts_on:
            raise InvalidValueError("end_before_start")
