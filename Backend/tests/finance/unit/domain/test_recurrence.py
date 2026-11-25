import uuid
from datetime import date

import pytest

from app.finance.domain.entities.recurrence import Recurrence
from app.finance.domain.exceptions import InvalidValueError
from app.finance.domain.services.next_occurrence import next_occurrence
from app.finance.domain.value_objects.account_id import AccountId
from app.finance.domain.value_objects.active_range import ActiveRange
from app.finance.domain.value_objects.category import Category
from app.finance.domain.value_objects.description import Description
from app.finance.domain.value_objects.frequency import Frequency
from app.finance.domain.value_objects.money import Money
from app.finance.domain.value_objects.owner_id import OwnerId
from app.finance.domain.value_objects.schedule import Schedule
from app.finance.domain.value_objects.transaction_kind import TransactionKind
from tests.finance.fakes.fake_recurrence_rules import FakeRecurrenceRules

REGRAS = FakeRecurrenceRules()
MENSAL_DIA_5 = Schedule(Frequency.MONTHLY, 5)


@pytest.mark.parametrize("dia", [0, 32, -1])
def test_dia_do_mes_fora_da_faixa_e_recusado(dia: int) -> None:
    with pytest.raises(InvalidValueError) as erro:
        Schedule(Frequency.MONTHLY, dia)

    assert erro.value.problem == "out_of_range"


@pytest.mark.parametrize("dia", [0, 8])
def test_dia_da_semana_fora_da_faixa_e_recusado(dia: int) -> None:
    with pytest.raises(InvalidValueError) as erro:
        Schedule(Frequency.WEEKLY, dia)

    assert erro.value.problem == "out_of_range"


@pytest.mark.parametrize(("frequencia", "dia"), [("monthly", 31), ("weekly", 7)])
def test_os_limites_da_faixa_sao_aceitos(frequencia: str, dia: int) -> None:
    assert Schedule(Frequency.parse(frequencia), dia).day == dia


def test_frequencia_desconhecida_e_recusada() -> None:
    with pytest.raises(InvalidValueError) as erro:
        Frequency.parse("yearly")

    assert erro.value.problem == "unknown"


def test_o_fim_antes_do_inicio_e_recusado() -> None:
    with pytest.raises(InvalidValueError) as erro:
        ActiveRange(date(2026, 12, 2), date(2026, 12, 1))

    assert erro.value.problem == "end_before_start"


def test_o_fim_no_mesmo_dia_do_inicio_e_aceito() -> None:
    assert ActiveRange(date(2026, 12, 1), date(2026, 12, 1)).ends_on is not None


def nova() -> Recurrence:
    return Recurrence.create(
        owner=OwnerId(uuid.uuid4()),
        account=AccountId.new(),
        kind=TransactionKind.EXPENSE,
        amount=Money(150000),
        description=Description("Aluguel"),
        category=None,
        schedule=MENSAL_DIA_5,
        window=ActiveRange(date(2026, 12, 1)),
    )


def test_recorrencias_sao_iguais_pelo_id() -> None:
    original = nova()
    mesma = nova()
    mesma.id = original.id
    mesma.description = Description("Outra descrição")

    assert original == mesma
    assert hash(original) == hash(mesma) == hash(original.id)
    assert len({original, mesma}) == 1


def test_recorrencias_com_ids_diferentes_nao_sao_iguais() -> None:
    a, b = nova(), nova()

    assert a != b
    assert len({a, b}) == 2


def test_recorrencia_nunca_e_igual_a_outro_tipo() -> None:
    recorrencia = nova()

    assert recorrencia != recorrencia.id
    assert recorrencia != "recorrencia"
    assert recorrencia.__eq__(object()) is False


def test_criar_recorrencia_guarda_todos_os_campos() -> None:
    dono = OwnerId(uuid.uuid4())
    conta = AccountId.new()
    categoria = Category("moradia")
    janela = ActiveRange(date(2026, 12, 1), date(2027, 12, 1))

    recorrencia = Recurrence.create(
        owner=dono,
        account=conta,
        kind=TransactionKind.EXPENSE,
        amount=Money(150000),
        description=Description("Aluguel"),
        category=categoria,
        schedule=MENSAL_DIA_5,
        window=janela,
    )

    assert recorrencia.owner == dono
    assert recorrencia.account == conta
    assert recorrencia.kind is TransactionKind.EXPENSE
    assert recorrencia.amount == Money(150000)
    assert recorrencia.description == Description("Aluguel")
    assert recorrencia.category == categoria
    assert recorrencia.schedule == MENSAL_DIA_5
    assert recorrencia.starts_on == date(2026, 12, 1)
    assert recorrencia.ends_on == date(2027, 12, 1)
    assert recorrencia.last_run_on is None


def test_revisar_troca_os_dados_e_mantem_a_identidade_e_o_dono() -> None:
    recorrencia = nova()
    id_antes, dono = recorrencia.id, recorrencia.owner
    outra_conta = AccountId.new()
    outra_categoria = Category("mercado")

    recorrencia.revise(
        account=outra_conta,
        kind=TransactionKind.INCOME,
        amount=Money(1),
        description=Description("Outra"),
        category=outra_categoria,
        schedule=Schedule(Frequency.WEEKLY, 2),
        window=ActiveRange(date(2027, 1, 1), date(2027, 2, 1)),
    )

    assert recorrencia.id == id_antes
    assert recorrencia.owner == dono
    assert recorrencia.account == outra_conta
    assert recorrencia.kind is TransactionKind.INCOME
    assert recorrencia.amount == Money(1)
    assert recorrencia.description == Description("Outra")
    assert recorrencia.category == outra_categoria
    assert recorrencia.schedule == Schedule(Frequency.WEEKLY, 2)
    assert recorrencia.starts_on == date(2027, 1, 1)
    assert recorrencia.ends_on == date(2027, 2, 1)


def test_cada_recorrencia_tem_identidade_propria() -> None:
    assert nova().id != nova().id


def proxima(
    hoje: date,
    comeca: date = date(2026, 1, 1),
    termina: date | None = None,
    schedule: Schedule = MENSAL_DIA_5,
    limite: int = 62,
) -> date | None:
    return next_occurrence(schedule, comeca, termina, hoje, REGRAS, limite)


def test_comeca_em_hoje_quando_hoje_e_dia_da_regra() -> None:
    assert proxima(date(2026, 12, 5)) == date(2026, 12, 5)


def test_procura_a_partir_de_hoje() -> None:
    assert proxima(date(2026, 12, 6)) == date(2027, 1, 5)


def test_comeca_em_max_de_hoje_e_do_inicio() -> None:
    assert proxima(date(2026, 11, 20), comeca=date(2026, 12, 10)) == date(2027, 1, 5)


def test_respeita_o_fim_e_devolve_none_depois_dele() -> None:
    assert proxima(date(2026, 12, 1), termina=date(2026, 12, 31)) == date(2026, 12, 5)
    assert proxima(date(2026, 12, 5), termina=date(2026, 12, 5)) == date(2026, 12, 5)
    assert proxima(date(2026, 12, 6), termina=date(2026, 12, 31)) is None


def test_recorrencia_ja_terminada_nao_tem_proxima() -> None:
    assert proxima(date(2027, 3, 1), termina=date(2026, 12, 31)) is None


def test_dia_31_em_fevereiro_cai_no_ultimo_dia() -> None:
    mensal_31 = Schedule(Frequency.MONTHLY, 31)

    assert proxima(date(2026, 2, 1), schedule=mensal_31) == date(2026, 2, 28)


def test_semanal_acha_a_proxima_segunda() -> None:
    segunda = Schedule(Frequency.WEEKLY, 1)

    assert proxima(date(2026, 11, 13), schedule=segunda) == date(2026, 11, 16)


def test_respeita_o_limite_de_dias_da_busca() -> None:
    assert proxima(date(2026, 12, 6), limite=10) is None
    assert proxima(date(2026, 12, 6), limite=31) == date(2027, 1, 5)
