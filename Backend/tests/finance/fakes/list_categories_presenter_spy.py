from app.finance.application.dtos.list_categories import CategoryOutput


class ListCategoriesPresenterSpy:
    def __init__(self) -> None:
        self.categories: tuple[CategoryOutput, ...] | None = None

    def present_categories(self, categories: tuple[CategoryOutput, ...]) -> None:
        self.categories = categories
