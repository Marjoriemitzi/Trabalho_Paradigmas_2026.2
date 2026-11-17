from fastapi import status
from fastapi.responses import JSONResponse

from app.finance.application.dtos.list_categories import CategoryOutput
from app.finance.application.use_cases.list_categories import (
    ListCategoriesOutputPort,
)
from app.finance.presentation.api.v1.schemas.categories import (
    CategoryListResponse,
    CategoryResponse,
)


class ListCategoriesHttpPresenter(ListCategoriesOutputPort):
    def __init__(self) -> None:
        self._response: JSONResponse | None = None

    def response(self) -> JSONResponse:
        if self._response is None:
            raise RuntimeError("O caso de uso terminou sem apresentar um resultado.")
        return self._response

    def present_categories(self, categories: tuple[CategoryOutput, ...]) -> None:
        corpo = CategoryListResponse(
            categories=[CategoryResponse.from_output(c) for c in categories]
        ).model_dump()
        self._response = JSONResponse(corpo, status_code=status.HTTP_200_OK)
