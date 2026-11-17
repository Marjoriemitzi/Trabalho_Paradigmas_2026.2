import pytest

from app.finance.domain.repositories.category_catalog import CategoryCatalog
from app.finance.domain.value_objects.category import Category
from app.finance.domain.value_objects.category_entry import CategoryEntry
from app.finance.domain.value_objects.transaction_kind import TransactionKind

RECEITA, DESPESA = TransactionKind.INCOME, TransactionKind.EXPENSE


class CategoryCatalogContract:
    @pytest.fixture
    def catalog(self) -> CategoryCatalog:
        raise NotImplementedError

    async def test_cada_categoria_vem_com_o_tipo_e_o_nome_para_mostrar(
        self, catalog: CategoryCatalog
    ) -> None:
        categorias = await catalog.list_all()

        assert CategoryEntry(DESPESA, Category("saude"), "Saúde") in categorias
        assert CategoryEntry(RECEITA, Category("salario"), "Salário") in categorias

    async def test_outros_existe_nos_dois_tipos(self, catalog: CategoryCatalog) -> None:
        assert await catalog.contains(DESPESA, Category("outros"))
        assert await catalog.contains(RECEITA, Category("outros"))

    async def test_a_lista_vem_por_tipo_e_depois_por_nome(
        self, catalog: CategoryCatalog
    ) -> None:
        categorias = await catalog.list_all()

        chaves = [(c.kind.value, c.category.name) for c in categorias]
        assert chaves == sorted(chaves)

    async def test_categoria_do_tipo_certo_existe(
        self, catalog: CategoryCatalog
    ) -> None:
        assert await catalog.contains(DESPESA, Category("mercado"))

    async def test_categoria_de_outro_tipo_nao_existe(
        self, catalog: CategoryCatalog
    ) -> None:
        assert not await catalog.contains(DESPESA, Category("salario"))
        assert not await catalog.contains(RECEITA, Category("mercado"))

    async def test_categoria_fora_da_lista_nao_existe(
        self, catalog: CategoryCatalog
    ) -> None:
        assert not await catalog.contains(DESPESA, Category("mercdo"))
