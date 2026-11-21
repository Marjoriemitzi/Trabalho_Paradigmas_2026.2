import calendar
from datetime import date

import pytest

from app.finance.domain.services.recurrence_rules import RecurrenceRules
from app.finance.domain.value_objects.frequency import Frequency
from app.finance.domain.value_objects.schedule import Schedule

MENSAL, SEMANAL = Frequency.MONTHLY, Frequency.WEEKLY


class RecurrenceRulesContract:
    @pytest.fixture
    def rules(self) -> RecurrenceRules:
        raise NotImplementedError

    @pytest.mark.parametrize(
        ("frequencia", "dia", "data", "esperado"),
        [
            (MENSAL, 5, date(2026, 12, 5), True),
            (MENSAL, 31, date(2026, 2, 28), True),
            (MENSAL, 31, date(2028, 2, 28), False),
            (MENSAL, 31, date(2028, 2, 29), True),
            (MENSAL, 30, date(2026, 4, 30), True),
            (MENSAL, 5, date(2026, 12, 6), False),
            (SEMANAL, 1, date(2026, 11, 16), True),
            (SEMANAL, 1, date(2026, 11, 13), False),
            (SEMANAL, 7, date(2026, 11, 22), True),
        ],
    )
    def test_tabela_da_regra(
        self,
        rules: RecurrenceRules,
        frequencia: Frequency,
        dia: int,
        data: date,
        esperado: bool,  # noqa: FBT001
    ) -> None:
        assert rules.is_due(Schedule(frequencia, dia), data) is esperado

    @pytest.mark.parametrize("ano", [2026, 2028])
    def test_dia_31_cai_no_ultimo_dia_de_todos_os_meses(
        self, rules: RecurrenceRules, ano: int
    ) -> None:
        for mes in range(1, 13):
            ultimo = calendar.monthrange(ano, mes)[1]
            ocorrencias = [
                dia
                for dia in range(1, ultimo + 1)
                if rules.is_due(Schedule(MENSAL, 31), date(ano, mes, dia))
            ]
            assert ocorrencias == [ultimo]
