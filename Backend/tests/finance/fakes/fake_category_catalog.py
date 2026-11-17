from app.finance.domain.value_objects.category import Category
from app.finance.domain.value_objects.category_entry import CategoryEntry
from app.finance.domain.value_objects.transaction_kind import TransactionKind

RECEITA, DESPESA = TransactionKind.INCOME, TransactionKind.EXPENSE

CATEGORIAS_PADRAO = (
    CategoryEntry(DESPESA, Category("lazer"), "Lazer"),
    CategoryEntry(DESPESA, Category("mercado"), "Mercado"),
    CategoryEntry(DESPESA, Category("moradia"), "Moradia"),
    CategoryEntry(DESPESA, Category("outros"), "Outros"),
    CategoryEntry(DESPESA, Category("saude"), "Saúde"),
    CategoryEntry(DESPESA, Category("transporte"), "Transporte"),
    CategoryEntry(RECEITA, Category("freelance"), "Freelance"),
    CategoryEntry(RECEITA, Category("outros"), "Outros"),
    CategoryEntry(RECEITA, Category("salario"), "Salário"),
)


class FakeCategoryCatalog:
    def __init__(self, entries: tuple[CategoryEntry, ...] = CATEGORIAS_PADRAO) -> None:
        self.entries = entries

    async def list_all(self) -> list[CategoryEntry]:
        return sorted(self.entries, key=lambda e: (e.kind.value, e.category.name))

    async def contains(self, kind: TransactionKind, category: Category) -> bool:
        return any(e.kind is kind and e.category == category for e in self.entries)
