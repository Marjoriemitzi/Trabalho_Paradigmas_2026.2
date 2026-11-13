from dataclasses import dataclass

from app.finance.domain.value_objects.category import Category
from app.finance.domain.value_objects.transaction_kind import TransactionKind


@dataclass(frozen=True, slots=True)
class CategoryEntry:
    kind: TransactionKind
    category: Category
    label: str
