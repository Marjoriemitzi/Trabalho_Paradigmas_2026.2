from dataclasses import dataclass

from app.finance.domain.exceptions import InvalidValueError


@dataclass(frozen=True, slots=True)
class Money:
    cents: int

    def __post_init__(self) -> None:
        if self.cents <= 0:
            raise InvalidValueError("not_positive")
