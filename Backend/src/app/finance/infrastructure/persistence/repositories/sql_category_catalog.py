from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.finance.domain.value_objects.category import Category
from app.finance.domain.value_objects.category_entry import CategoryEntry
from app.finance.domain.value_objects.transaction_kind import TransactionKind
from app.finance.infrastructure.persistence.models.category_model import CategoryModel


class SqlCategoryCatalog:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def list_all(self) -> list[CategoryEntry]:
        consulta = select(CategoryModel).order_by(
            CategoryModel.kind, CategoryModel.name
        )
        return [
            CategoryEntry(
                kind=TransactionKind(m.kind), category=Category(m.name), label=m.label
            )
            for m in await self._session.scalars(consulta)
        ]

    async def contains(self, kind: TransactionKind, category: Category) -> bool:
        consulta = select(CategoryModel.name).where(
            CategoryModel.kind == kind.value, CategoryModel.name == category.name
        )
        return await self._session.scalar(consulta) is not None
