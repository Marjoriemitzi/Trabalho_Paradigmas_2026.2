from app.finance.domain.value_objects.category import Category
from app.finance.domain.value_objects.description import Description
from app.finance.domain.value_objects.transaction_kind import TransactionKind


class FakeCategorizer:
    def __init__(self, answer: Category) -> None:
        self._answer = answer
        self.asked: list[tuple[TransactionKind, Description]] = []

    def categorize(self, kind: TransactionKind, description: Description) -> Category:
        self.asked.append((kind, description))
        return self._answer
