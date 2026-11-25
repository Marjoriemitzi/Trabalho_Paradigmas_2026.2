import calendar
import uuid
from datetime import date, timedelta

import pytest
from hypothesis import given
from hypothesis import strategies as st

from app.finance.domain.entities.recurrence import Recurrence
from app.finance.domain.services.next_occurrence import next_occurrence
from app.finance.domain.services.pending_run import PendingRun, pending_run
from app.finance.domain.value_objects.account_id import AccountId
from app.finance.domain.value_objects.active_range import ActiveRange
from app.finance.domain.value_objects.description import Description
from app.finance.domain.value_objects.frequency import Frequency
from app.finance.domain.value_objects.money import Money
from app.finance.domain.value_objects.owner_id import OwnerId
from app.finance.domain.value_objects.schedule import Schedule
from app.finance.domain.value_objects.transaction_kind import TransactionKind
from tests.finance.fakes.fake_recurrence_rules import FakeRecurrenceRules

pytestmark = pytest.mark.property

REGRAS = FakeRecurrenceRules()
JANELA_DE_RECUPERACAO = timedelta(days=61)

DATAS = st.dates(min_value=date(1990, 1, 1), max_value=date(2100, 12, 31))
AGENDAS = st.one_of(
    st.builds(Schedule, st.just(Frequency.MONTHLY), st.integers(1, 31)),
    st.builds(Schedule, st.just(Frequency.WEEKLY), st.integers(1, 7)),
)
FIM_OPCIONAL = st.one_of(st.none(), st.integers(min_value=0, max_value=400))


def _dias(inicio: date, deslocamento: int) -> date:
    return inicio + timedelta(days=deslocamento)


@st.composite
def _cenarios(draw: st.DrawFn) -> tuple[Recurrence, date]:
    """Uma recorrência qualquer e um `today` perto dela (antes, durante ou depois)."""
    agenda = draw(AGENDAS)
    inicio = draw(DATAS)
    fim_em = draw(FIM_OPCIONAL)
    fim = None if fim_em is None else _dias(inicio, fim_em)
    recorrencia = Recurrence.create(
        owner=OwnerId(uuid.uuid4()),
        account=AccountId.new(),
        kind=TransactionKind.EXPENSE,
        amount=Money(1000),
        description=Description("Assinatura"),
        category=None,
        schedule=agenda,
        window=ActiveRange(inicio, fim),
    )
    ultima_em = draw(st.one_of(st.none(), st.integers(-10, 400)))
    if ultima_em is not None:
        recorrencia.mark_run(_dias(inicio, ultima_em))
    hoje = _dias(inicio, draw(st.integers(min_value=-30, max_value=500)))
    return recorrencia, hoje


def _primeiro_pendente(recorrencia: Recurrence) -> date:
    if recorrencia.last_run_on is None:
        return recorrencia.starts_on
    return recorrencia.last_run_on + timedelta(days=1)


@given(cenario=_cenarios())
def test_pending_run_devolve_dias_crescentes_e_validos(
    cenario: tuple[Recurrence, date],
) -> None:
    r, hoje = cenario

    execucao = pending_run(r, hoje, REGRAS)

    assert tuple(sorted(set(execucao.days))) == execucao.days
    for d in execucao.days:
        assert r.starts_on <= d <= hoje
        assert r.ends_on is None or d <= r.ends_on
        assert r.last_run_on is None or d > r.last_run_on
        assert d >= hoje - JANELA_DE_RECUPERACAO
        assert REGRAS.is_due(r.schedule, d)


@given(cenario=_cenarios())
def test_pending_run_nao_esquece_nenhum_dia_da_janela(
    cenario: tuple[Recurrence, date],
) -> None:
    r, hoje = cenario

    execucao = pending_run(r, hoje, REGRAS)

    if execucao.last_day is None:
        assert execucao.days == ()
        return
    inicio = max(_primeiro_pendente(r), hoje - JANELA_DE_RECUPERACAO)
    esperados = tuple(
        _dias(inicio, passo)
        for passo in range((execucao.last_day - inicio).days + 1)
        if REGRAS.is_due(r.schedule, _dias(inicio, passo))
    )
    assert execucao.days == esperados


@given(cenario=_cenarios())
def test_pending_run_so_pula_dias_antes_da_janela_de_recuperacao(
    cenario: tuple[Recurrence, date],
) -> None:
    r, hoje = cenario
    primeiro = _primeiro_pendente(r)
    ultimo = hoje if r.ends_on is None else min(hoje, r.ends_on)

    execucao = pending_run(r, hoje, REGRAS)

    assert execucao.skipped_days >= 0
    tem_pendencia = primeiro <= ultimo
    antes_da_janela = primeiro < hoje - JANELA_DE_RECUPERACAO
    assert (execucao.skipped_days > 0) is (tem_pendencia and antes_da_janela)
    if execucao.skipped_days > 0:
        assert execucao.skipped_days == (hoje - JANELA_DE_RECUPERACAO - primeiro).days


@given(cenario=_cenarios())
def test_pending_run_e_idempotente_depois_de_mark_run(
    cenario: tuple[Recurrence, date],
) -> None:
    r, hoje = cenario
    execucao = pending_run(r, hoje, REGRAS)
    if execucao.last_day is None:
        assert execucao == PendingRun(days=(), skipped_days=0, last_day=None)
        return

    r.mark_run(execucao.last_day)

    assert pending_run(r, hoje, REGRAS) == PendingRun(
        days=(), skipped_days=0, last_day=None
    )


@given(
    agenda=AGENDAS,
    inicio=DATAS,
    fim_em=FIM_OPCIONAL,
    desde_em=st.integers(min_value=-100, max_value=500),
    limite=st.integers(min_value=1, max_value=62),
)
def test_next_occurrence_devolve_a_primeira_data_devida_da_janela(
    agenda: Schedule,
    inicio: date,
    fim_em: int | None,
    desde_em: int,
    limite: int,
) -> None:
    fim = None if fim_em is None else _dias(inicio, fim_em)
    desde = _dias(inicio, desde_em)
    base = max(desde, inicio)

    d = next_occurrence(agenda, inicio, fim, desde, REGRAS, limit_days=limite)

    if d is None:
        ultimo_buscado = _dias(base, limite - 1)
        if fim is not None:
            ultimo_buscado = min(ultimo_buscado, fim)
        assert not any(
            REGRAS.is_due(agenda, _dias(base, passo))
            for passo in range((ultimo_buscado - base).days + 1)
        )
        return
    assert d >= base
    assert fim is None or d <= fim
    assert (d - base).days < limite
    assert REGRAS.is_due(agenda, d)
    assert not any(
        REGRAS.is_due(agenda, _dias(base, passo)) for passo in range((d - base).days)
    )


@given(dia_pedido=st.integers(1, 31), inicio=DATAS, desde=DATAS)
def test_next_occurrence_mensal_sem_fim_sempre_acha_o_dia_ajustado_ao_mes(
    dia_pedido: int, inicio: date, desde: date
) -> None:
    d = next_occurrence(
        Schedule(Frequency.MONTHLY, dia_pedido), inicio, None, desde, REGRAS, 62
    )

    assert d is not None
    assert d.day == min(dia_pedido, calendar.monthrange(d.year, d.month)[1])
