from typing import Protocol

from app.finance.domain.value_objects.category import Category
from app.finance.domain.value_objects.category_entry import CategoryEntry
from app.finance.domain.value_objects.transaction_kind import TransactionKind


class CategoryCatalog(Protocol):
    async def list_all(self) -> list[CategoryEntry]: ...

    async def contains(self, kind: TransactionKind, category: Category) -> bool: ...
