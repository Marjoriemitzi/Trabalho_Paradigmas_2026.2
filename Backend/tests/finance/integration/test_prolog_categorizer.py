from pathlib import Path

import pytest

from app.finance.domain.exceptions import InvalidValueError
from app.finance.domain.services.categorizer import Categorizer
from app.finance.domain.value_objects.category import Category
from app.finance.domain.value_objects.description import MAX_LENGTH, Description
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


@pytest.mark.parametrize(
    ("kind", "texto", "esperada"),
    [
        (DESPESA, "'supermercado'", "mercado"),
        (DESPESA, '"padaria"', "mercado"),
        (DESPESA, "'mercado' \"extra\" '\\'", "mercado"),
        (DESPESA, "compra \\ supermercado \\\\ fim", "mercado"),
        (DESPESA, "linha1\n\r\tsupermercado\t\nlinha2", "mercado"),
        (DESPESA, "compra\x01supermercado\x1f", "mercado"),
        (
            DESPESA,
            'mercado"), assertz(category_keyword(expense, hack, ["x"])),'
            ' transaction_category("',
            "mercado",
        ),
        (DESPESA, "supermercado' ; true ; '", "mercado"),
        (DESPESA, ":- halt.", "outros"),
        (DESPESA, "Supermercado 🛒", "mercado"),
        (RECEITA, "SÁLÁRIO\u0301", "salario"),
        (
            DESPESA,
            "\uff33\uff55\uff50\uff45\uff52\uff4d\uff45\uff52\uff43\uff41\uff44\uff4f",
            "mercado",
        ),
        (DESPESA, "a", "outros"),
        (DESPESA, "a" * MAX_LENGTH, "outros"),
        (DESPESA, ("x" * (MAX_LENGTH - len("padaria!"))) + "padaria!", "mercado"),
    ],
)
def test_entradas_adversariais_e_limites_retornam_categoria_valida(
    categorizer: Categorizer, kind: TransactionKind, texto: str, esperada: str
) -> None:
    categoria = categorizer.categorize(kind, Description(texto))

    assert categoria == Category(esperada)


def test_tentativa_de_assertz_nao_contamina_consultas_seguintes(
    categorizer: Categorizer,
) -> None:
    ataque = (
        'mercado"), assertz(category_keyword(expense, hack, ["x"])),'
        ' transaction_category("'
    )
    assert categorizer.categorize(DESPESA, Description(ataque)) == Category("mercado")

    subsequente = categorizer.categorize(DESPESA, Description("x"))

    assert subsequente == Category("outros")


def test_descricao_com_byte_nul_e_recusada_na_borda() -> None:
    with pytest.raises(InvalidValueError) as erro:
        Description("foo\x00supermercado")

    assert erro.value.problem == "invalid_format"
