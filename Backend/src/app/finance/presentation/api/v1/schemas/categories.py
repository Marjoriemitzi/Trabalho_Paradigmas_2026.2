from typing import Self

from pydantic import BaseModel

from app.finance.application.dtos.list_categories import CategoryOutput


class CategoryResponse(BaseModel):
    kind: str
    name: str
    label: str

    @classmethod
    def from_output(cls, category: CategoryOutput) -> Self:
        return cls(kind=category.kind, name=category.name, label=category.label)


class CategoryListResponse(BaseModel):
    categories: list[CategoryResponse]
