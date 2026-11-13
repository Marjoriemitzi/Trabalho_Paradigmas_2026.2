from typing import Protocol

from app.finance.domain.value_objects.category import Category
from app.finance.domain.value_objects.description import Description
from app.finance.domain.value_objects.transaction_kind import TransactionKind


class Categorizer(Protocol):
    def categorize(
        self, kind: TransactionKind, description: Description
    ) -> Category: ...
