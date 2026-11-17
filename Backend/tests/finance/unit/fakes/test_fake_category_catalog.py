import pytest

from app.finance.domain.repositories.category_catalog import CategoryCatalog
from tests.finance.contracts.category_catalog_contract import CategoryCatalogContract
from tests.finance.fakes.fake_category_catalog import FakeCategoryCatalog


class TestFakeCategoryCatalog(CategoryCatalogContract):
    @pytest.fixture
    def catalog(self) -> CategoryCatalog:
        return FakeCategoryCatalog()
