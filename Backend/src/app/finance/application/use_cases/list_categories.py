from dataclasses import dataclass
from typing import Protocol

from app.finance.application.dtos.list_categories import CategoryOutput
from app.finance.application.ports.unit_of_work import UnitOfWork


class ListCategoriesInputPort(Protocol):
    async def execute(self) -> None: ...


class ListCategoriesOutputPort(Protocol):
    def present_categories(self, categories: tuple[CategoryOutput, ...]) -> None: ...


@dataclass(frozen=True, slots=True)
class ListCategoriesInteractor(ListCategoriesInputPort):
    uow: UnitOfWork
    presenter: ListCategoriesOutputPort

    async def execute(self) -> None:
        async with self.uow:
            categorias = await self.uow.categories.list_all()
        self.presenter.present_categories(
            tuple(CategoryOutput.from_entry(c) for c in categorias)
        )
