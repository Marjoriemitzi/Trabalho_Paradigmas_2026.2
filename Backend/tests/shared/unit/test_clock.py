from datetime import UTC, date, datetime
from zoneinfo import ZoneInfo

from app.shared.domain.clock import Clock
from app.shared.infrastructure.clock import ZoneInfoClock
from tests.shared.fakes.fixed_clock import FixedClock

SAO_PAULO = ZoneInfo("America/Sao_Paulo")


def relogio(agora_utc: datetime) -> Clock:
    return ZoneInfoClock(SAO_PAULO, now=lambda: agora_utc)


def test_perto_da_meia_noite_o_dia_e_o_do_fuso_e_nao_o_do_utc() -> None:
    agora = datetime(2026, 11, 14, 1, 30, tzinfo=UTC)

    assert relogio(agora).today() == date(2026, 11, 13)


def test_depois_da_meia_noite_do_fuso_ja_e_o_dia_seguinte() -> None:
    agora = datetime(2026, 11, 14, 3, 0, tzinfo=UTC)

    assert relogio(agora).today() == date(2026, 11, 14)


def test_o_relogio_real_devolve_uma_data() -> None:
    assert isinstance(ZoneInfoClock(SAO_PAULO).today(), date)


def test_o_relogio_fixo_devolve_sempre_o_mesmo_dia_e_avanca_quando_pedido() -> None:
    relogio_fixo = FixedClock(date(2026, 11, 20))

    assert relogio_fixo.today() == date(2026, 11, 20)
    relogio_fixo.advance(12)
    assert relogio_fixo.today() == date(2026, 12, 2)
