import uuid
from datetime import date

from app.finance.domain.entities.recurrence import Recurrence
from app.finance.domain.services.pending_run import pending_run
from app.finance.domain.value_objects.account_id import AccountId
from app.finance.domain.value_objects.active_range import ActiveRange
from app.finance.domain.value_objects.description import Description
from app.finance.domain.value_objects.frequency import Frequency
from app.finance.domain.value_objects.money import Money
from app.finance.domain.value_objects.owner_id import OwnerId
from app.finance.domain.value_objects.schedule import Schedule
from app.finance.domain.value_objects.transaction_kind import TransactionKind
from tests.finance.fakes.fake_recurrence_rules import FakeRecurrenceRules

REGRAS = FakeRecurrenceRules()


def recorrencia(
    schedule: Schedule,
    comeca_em: date,
    termina_em: date | None = None,
    ultima: date | None = None,
) -> Recurrence:
    r = Recurrence.create(
        owner=OwnerId(uuid.uuid4()),
        account=AccountId.new(),
        kind=TransactionKind.EXPENSE,
        amount=Money(1000),
        description=Description("Teste"),
        category=None,
        schedule=schedule,
        window=ActiveRange(comeca_em, termina_em),
    )
    if ultima is not None:
        r.mark_run(ultima)
    return r


MENSAL_5 = Schedule(Frequency.MONTHLY, 5)
SEMANAL_SEG = Schedule(Frequency.WEEKLY, 1)


def test_nunca_rodou_comeca_em_starts_on() -> None:
    r = recorrencia(MENSAL_5, date(2026, 11, 1))

    execucao = pending_run(r, date(2026, 12, 20), REGRAS)

    assert execucao.days == (date(2026, 11, 5), date(2026, 12, 5))
    assert execucao.skipped_days == 0
    assert execucao.last_day == date(2026, 12, 20)


def test_rodou_ontem_so_olha_hoje() -> None:
    r = recorrencia(MENSAL_5, date(2026, 1, 1), ultima=date(2026, 12, 4))

    execucao = pending_run(r, date(2026, 12, 5), REGRAS)

    assert execucao.days == (date(2026, 12, 5),)
    assert execucao.last_day == date(2026, 12, 5)


def test_ja_processada_hoje_nao_tem_nada_a_lancar() -> None:
    r = recorrencia(MENSAL_5, date(2026, 1, 1), ultima=date(2026, 12, 5))

    execucao = pending_run(r, date(2026, 12, 5), REGRAS)

    assert execucao.days == ()
    assert execucao.last_day is None


def test_o_fim_no_meio_da_janela_corta_as_datas_e_o_ultimo_dia() -> None:
    r = recorrencia(SEMANAL_SEG, date(2026, 12, 1), termina_em=date(2026, 12, 15))

    execucao = pending_run(r, date(2026, 12, 31), REGRAS)

    assert execucao.days == (date(2026, 12, 7), date(2026, 12, 14))
    assert execucao.last_day == date(2026, 12, 15)


def test_comeco_no_futuro_nao_lanca_nada() -> None:
    r = recorrencia(MENSAL_5, date(2027, 1, 1))

    assert pending_run(r, date(2026, 12, 20), REGRAS).days == ()


def test_o_limite_de_62_dias_pula_o_que_e_mais_antigo_e_conta_os_dias() -> None:
    r = recorrencia(Schedule(Frequency.MONTHLY, 1), date(2026, 1, 1))
    hoje = date(2026, 12, 20)

    execucao = pending_run(r, hoje, REGRAS)

    # 62 dias terminando em hoje: de 2026-10-20 até 2026-12-20
    assert execucao.days == (date(2026, 11, 1), date(2026, 12, 1))
    primeiro_dia_pulado = (date(2026, 10, 20) - date(2026, 1, 1)).days
    assert execucao.skipped_days == primeiro_dia_pulado


def test_dia_31_em_fevereiro_cai_no_ultimo_dia() -> None:
    r = recorrencia(Schedule(Frequency.MONTHLY, 31), date(2026, 2, 1))

    execucao = pending_run(r, date(2026, 3, 1), REGRAS)

    assert execucao.days == (date(2026, 2, 28),)


def test_marcar_a_execucao_guarda_o_dia() -> None:
    r = recorrencia(MENSAL_5, date(2026, 1, 1))

    r.mark_run(date(2026, 12, 5))

    assert r.last_run_on == date(2026, 12, 5)
