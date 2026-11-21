from datetime import date, timedelta

from app.finance.domain.services.recurrence_rules import RecurrenceRules
from app.finance.domain.value_objects.schedule import Schedule

SEARCH_LIMIT_DAYS = 62


def next_occurrence(
    schedule: Schedule,
    starts_on: date,
    ends_on: date | None,
    from_day: date,
    rules: RecurrenceRules,
    limit_days: int = SEARCH_LIMIT_DAYS,
) -> date | None:
    """A primeira data da regra a partir de `from_day`, entre `starts_on` e `ends_on`.

    O Prolog decide, dia a dia, por no máximo `limit_days` dias. Sem achar, ou depois
    do fim da recorrência, devolve None.
    """
    primeiro = max(from_day, starts_on)
    for passo in range(limit_days):
        dia = primeiro + timedelta(days=passo)
        if ends_on is not None and dia > ends_on:
            return None
        if rules.is_due(schedule, dia):
            return dia
    return None
