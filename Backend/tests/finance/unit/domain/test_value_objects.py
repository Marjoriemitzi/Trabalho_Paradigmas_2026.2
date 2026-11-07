import pytest

from app.finance.domain.exceptions import InvalidValueError
from app.finance.domain.value_objects.category import Category
from app.finance.domain.value_objects.description import Description
from app.finance.domain.value_objects.money import Money
from app.finance.domain.value_objects.transaction_kind import TransactionKind


def test_dinheiro_guarda_centavos_inteiros() -> None:
    assert Money(1250).cents == 1250


def test_dinheiro_nao_pode_ser_zero_nem_negativo() -> None:
    for invalido in (0, -1):
        with pytest.raises(InvalidValueError) as erro:
            Money(invalido)
        assert erro.value.problem == "not_positive"


def test_tipo_da_transacao_vem_do_texto() -> None:
    assert TransactionKind.parse("income") is TransactionKind.INCOME
    assert TransactionKind.parse("expense") is TransactionKind.EXPENSE


def test_tipo_desconhecido_e_recusado() -> None:
    with pytest.raises(InvalidValueError) as erro:
        TransactionKind.parse("transfer")
    assert erro.value.problem == "unknown"


def test_descricao_perde_os_espacos_das_pontas() -> None:
    assert Description("  Supermercado  ").text == "Supermercado"


def test_descricao_em_branco_e_recusada() -> None:
    with pytest.raises(InvalidValueError) as erro:
        Description("   ")
    assert erro.value.problem == "blank"


def test_descricao_tem_no_maximo_200_caracteres() -> None:
    assert Description("a" * 200).text == "a" * 200
    with pytest.raises(InvalidValueError) as erro:
        Description("a" * 201)
    assert erro.value.problem == "too_long"


def test_categoria_e_um_nome_curto_em_minusculas() -> None:
    assert Category(" Mercado ").name == "mercado"


def test_categoria_com_caracteres_estranhos_e_recusada() -> None:
    for invalida in ("", "lazer e cultura", "café", "1mercado", "a" * 41):
        with pytest.raises(InvalidValueError) as erro:
            Category(invalida)
        assert erro.value.problem == "invalid_format", invalida
