from dataclasses import dataclass
from typing import Self

from app.finance.domain.value_objects.category_entry import CategoryEntry


@dataclass(frozen=True, slots=True)
class CategoryOutput:
    kind: str
    name: str
    label: str

    @classmethod
    def from_entry(cls, entry: CategoryEntry) -> Self:
        return cls(kind=entry.kind.value, name=entry.category.name, label=entry.label)
