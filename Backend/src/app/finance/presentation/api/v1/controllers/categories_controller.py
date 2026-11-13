from collections.abc import Callable
from dataclasses import dataclass

from fastapi.responses import JSONResponse

from app.finance.application.use_cases.list_categories import (
    ListCategoriesInputPort,
    ListCategoriesOutputPort,
)
from app.finance.presentation.api.v1.presenters.list_categories_presenter import (
    ListCategoriesHttpPresenter,
)

ListCategoriesFactory = Callable[[ListCategoriesOutputPort], ListCategoriesInputPort]


@dataclass(frozen=True, slots=True)
class ListCategoriesController:
    build_interactor: ListCategoriesFactory

    async def handle(self) -> JSONResponse:
        presenter = ListCategoriesHttpPresenter()
        await self.build_interactor(presenter).execute()
        return presenter.response()
