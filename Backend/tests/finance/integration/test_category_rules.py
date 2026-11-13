from pathlib import Path

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.finance.domain.value_objects.transaction_kind import TransactionKind
from app.finance.infrastructure.persistence.repositories.sql_category_catalog import (
    SqlCategoryCatalog,
)
from app.shared.infrastructure.prolog.gateway import PrologGateway

RULES_DIR = Path(__file__).resolve().parents[3] / "rules"


@pytest.fixture(scope="module")
def regras() -> PrologGateway:
    gateway = PrologGateway()
    gateway.consult(RULES_DIR / "finance" / "categorization.pl")
    return gateway


@pytest.mark.parametrize("kind", list(TransactionKind), ids=lambda k: k.value)
async def test_as_regras_so_escolhem_categorias_da_lista(
    regras: PrologGateway, session: AsyncSession, kind: TransactionKind
) -> None:
    escolhas = set(regras.values("category_choice", kind.value))
    na_lista = {
        e.category.name
        for e in await SqlCategoryCatalog(session).list_all()
        if e.kind is kind
    }

    assert "outros" in escolhas
    assert escolhas <= na_lista, f"Fora da lista: {sorted(escolhas - na_lista)}"
