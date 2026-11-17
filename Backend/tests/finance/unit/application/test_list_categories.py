from app.finance.application.dtos.list_categories import CategoryOutput
from app.finance.application.use_cases.list_categories import ListCategoriesInteractor
from app.finance.domain.value_objects.category import Category
from app.finance.domain.value_objects.category_entry import CategoryEntry
from app.finance.domain.value_objects.transaction_kind import TransactionKind
from tests.finance.fakes.fake_category_catalog import FakeCategoryCatalog
from tests.finance.fakes.fake_unit_of_work import FakeUnitOfWork
from tests.finance.fakes.list_categories_presenter_spy import (
    ListCategoriesPresenterSpy,
)


def montar() -> (
    tuple[ListCategoriesInteractor, FakeUnitOfWork, ListCategoriesPresenterSpy]
):
    uow = FakeUnitOfWork()
    uow.categories = FakeCategoryCatalog(
        (
            CategoryEntry(TransactionKind.INCOME, Category("salario"), "Salário"),
            CategoryEntry(TransactionKind.EXPENSE, Category("saude"), "Saúde"),
        )
    )
    presenter = ListCategoriesPresenterSpy()
    return ListCategoriesInteractor(uow=uow, presenter=presenter), uow, presenter


async def test_lista_cada_categoria_com_tipo_nome_e_rotulo() -> None:
    interactor, _, presenter = montar()

    await interactor.execute()

    assert presenter.categories == (
        CategoryOutput(kind="expense", name="saude", label="Saúde"),
        CategoryOutput(kind="income", name="salario", label="Salário"),
    )


async def test_listar_nao_grava_nada() -> None:
    interactor, uow, _ = montar()

    await interactor.execute()

    assert uow.committed is False
