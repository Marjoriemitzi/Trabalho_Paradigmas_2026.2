from dataclasses import dataclass
from datetime import date, timedelta

from app.finance.domain.entities.recurrence import Recurrence
from app.finance.domain.services.recurrence_rules import RecurrenceRules

RECOVERY_LIMIT_DAYS = 62


@dataclass(frozen=True, slots=True)
class PendingRun:
    days: tuple[date, ...]
    skipped_days: int
    last_day: date | None


def pending_run(
    recurrence: Recurrence,
    today: date,
    rules: RecurrenceRules,
    limit_days: int = RECOVERY_LIMIT_DAYS,
) -> PendingRun:
    """As datas a lançar até `today`, com o limite de recuperação.

    Começa no dia seguinte à última execução (ou em `starts_on`) e termina em `today` ou
    `ends_on`. Dias mais antigos que `limit_days` são pulados e só contados.
    """
    primeiro = (
        recurrence.starts_on
        if recurrence.last_run_on is None
        else recurrence.last_run_on + timedelta(days=1)
    )
    ultimo = today if recurrence.ends_on is None else min(today, recurrence.ends_on)
    if primeiro > ultimo:
        return PendingRun(days=(), skipped_days=0, last_day=None)

    mais_antigo = today - timedelta(days=limit_days - 1)
    inicio = max(primeiro, mais_antigo)
    pulados = max(0, (inicio - primeiro).days)
    dias: list[date] = []
    dia = inicio
    while dia <= ultimo:
        if rules.is_due(recurrence.schedule, dia):
            dias.append(dia)
        dia += timedelta(days=1)
    return PendingRun(days=tuple(dias), skipped_days=pulados, last_day=ultimo)
