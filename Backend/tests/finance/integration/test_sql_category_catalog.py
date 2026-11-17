import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.finance.domain.repositories.category_catalog import CategoryCatalog
from app.finance.infrastructure.persistence.repositories.sql_category_catalog import (
    SqlCategoryCatalog,
)
from tests.finance.contracts.category_catalog_contract import CategoryCatalogContract
from tests.finance.fakes.fake_category_catalog import CATEGORIAS_PADRAO


class TestSqlCategoryCatalog(CategoryCatalogContract):
    @pytest.fixture
    def catalog(self, session: AsyncSession) -> CategoryCatalog:
        return SqlCategoryCatalog(session)


async def test_o_fake_tem_as_mesmas_categorias_do_banco(session: AsyncSession) -> None:
    no_banco = await SqlCategoryCatalog(session).list_all()

    assert no_banco == sorted(
        CATEGORIAS_PADRAO, key=lambda e: (e.kind.value, e.category.name)
    )
