from dataclasses import dataclass

from app.finance.domain.exceptions import InvalidValueError
from app.finance.domain.value_objects.category import Category


@dataclass(frozen=True, slots=True)
class CategoryTotal:
    category: Category
    total_cents: int
    count: int

    def __post_init__(self) -> None:
        if self.count < 1 or self.total_cents < 1:
            raise InvalidValueError("empty")

    @property
    def average_cents(self) -> int:
        return (self.total_cents + self.count // 2) // self.count
