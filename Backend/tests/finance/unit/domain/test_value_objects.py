from datetime import date

import pytest

from app.finance.domain.exceptions import InvalidValueError
from app.finance.domain.value_objects.category import Category
from app.finance.domain.value_objects.category_total import CategoryTotal
from app.finance.domain.value_objects.description import Description
from app.finance.domain.value_objects.money import Money
from app.finance.domain.value_objects.period import Period
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


def test_periodo_inclui_o_primeiro_e_o_ultimo_dia() -> None:
    novembro = Period(date(2026, 11, 1), date(2026, 11, 30))

    assert novembro.contains(date(2026, 11, 1))
    assert novembro.contains(date(2026, 11, 30))
    assert not novembro.contains(date(2026, 10, 31))
    assert not novembro.contains(date(2026, 12, 1))


def test_periodo_que_termina_antes_de_comecar_e_recusado() -> None:
    with pytest.raises(InvalidValueError) as erro:
        Period(date(2026, 11, 30), date(2026, 11, 1))
    assert erro.value.problem == "end_before_start"


def test_periodo_tem_no_maximo_um_ano() -> None:
    assert Period(date(2028, 1, 1), date(2028, 12, 31)).end == date(2028, 12, 31)
    with pytest.raises(InvalidValueError) as erro:
        Period(date(2028, 1, 1), date(2029, 1, 1))
    assert erro.value.problem == "too_long"


def test_total_da_categoria_calcula_a_media_arredondada() -> None:
    assert CategoryTotal(Category("mercado"), 1000, 3).average_cents == 333
    assert CategoryTotal(Category("mercado"), 1001, 2).average_cents == 501


@pytest.mark.parametrize(("total", "quantidade"), [(0, 0), (100, 0), (0, 1)])
def test_total_da_categoria_sem_lancamento_nao_existe(
    total: int, quantidade: int
) -> None:
    with pytest.raises(InvalidValueError) as erro:
        CategoryTotal(Category("mercado"), total, quantidade)
    assert erro.value.problem == "empty"
