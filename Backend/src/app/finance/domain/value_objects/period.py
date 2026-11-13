from dataclasses import dataclass
from datetime import date

from app.finance.domain.exceptions import InvalidValueError

MAX_DAYS = 366


@dataclass(frozen=True, slots=True)
class Period:
    start: date
    end: date

    def __post_init__(self) -> None:
        if self.end < self.start:
            raise InvalidValueError("end_before_start")
        if (self.end - self.start).days + 1 > MAX_DAYS:
            raise InvalidValueError("too_long")

    def contains(self, day: date) -> bool:
        return self.start <= day <= self.end
