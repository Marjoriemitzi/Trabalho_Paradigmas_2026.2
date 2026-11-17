from pathlib import Path

import pytest

from app.finance.domain.services.categorizer import Categorizer
from app.finance.domain.value_objects.category import Category
from app.finance.domain.value_objects.description import Description
from app.finance.domain.value_objects.transaction_kind import TransactionKind
from app.finance.infrastructure.prolog.prolog_categorizer import PrologCategorizer
from app.shared.infrastructure.prolog.gateway import PrologGateway

RULES_DIR = Path(__file__).resolve().parents[3] / "rules"
DESPESA = TransactionKind.EXPENSE
RECEITA = TransactionKind.INCOME


@pytest.fixture(scope="module")
def categorizer() -> Categorizer:
    return PrologCategorizer(PrologGateway(), RULES_DIR)


def test_despesa_no_supermercado_e_mercado(categorizer: Categorizer) -> None:
    categoria = categorizer.categorize(DESPESA, Description("Supermercado Extra"))
    assert categoria == Category("mercado")


def test_maiusculas_e_acentos_nao_atrapalham(categorizer: Categorizer) -> None:
    categoria = categorizer.categorize(RECEITA, Description("SALÁRIO de novembro"))
    assert categoria == Category("salario")


def test_o_tipo_importa_salario_nao_e_despesa(categorizer: Categorizer) -> None:
    categoria = categorizer.categorize(DESPESA, Description("Salário da diarista"))
    assert categoria == Category("outros")


def test_sem_palavra_conhecida_a_categoria_e_outros(categorizer: Categorizer) -> None:
    categoria = categorizer.categorize(DESPESA, Description("Presente de aniversário"))
    assert categoria == Category("outros")


def test_a_regra_da_uma_resposta_so(categorizer: Categorizer) -> None:
    categoria = categorizer.categorize(DESPESA, Description("Uber até o restaurante"))
    assert categoria == Category("transporte")
