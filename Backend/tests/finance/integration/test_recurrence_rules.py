from pathlib import Path

import pytest

from app.finance.domain.services.recurrence_rules import RecurrenceRules
from app.finance.infrastructure.prolog.prolog_recurrence_rules import (
    PrologRecurrenceRules,
)
from app.shared.infrastructure.prolog.gateway import PrologGateway
from tests.finance.contracts.recurrence_rules_contract import RecurrenceRulesContract

RULES_DIR = Path(__file__).resolve().parents[3] / "rules"


class TestPrologRecurrenceRules(RecurrenceRulesContract):
    @pytest.fixture
    def rules(self) -> RecurrenceRules:
        return PrologRecurrenceRules(PrologGateway(), RULES_DIR)


@pytest.fixture(scope="module")
def gateway() -> PrologGateway:
    prolog = PrologGateway()
    PrologRecurrenceRules(prolog, RULES_DIR)
    return prolog


@pytest.mark.parametrize(
    "frequencia",
    ["yearly", "daily", "monthly') ; true ; ('", "weekly), true ; (x", "", "MONTHLY"],
)
def test_frequencia_desconhecida_ou_adversarial_e_falsa_sem_erro(
    gateway: PrologGateway, frequencia: str
) -> None:
    assert gateway.holds("recurrence_due", frequencia, 5, 2026, 12, 5) is False


@pytest.mark.parametrize(
    ("ano", "mes", "dia", "esperado"),
    [
        (1900, 2, 28, True),
        (2000, 2, 28, False),
        (2000, 2, 29, True),
        (2100, 2, 28, True),
        (2400, 2, 29, True),
    ],
)
def test_consulta_direta_de_fevereiro_nos_anos_seculares(
    gateway: PrologGateway,
    ano: int,
    mes: int,
    dia: int,
    esperado: bool,  # noqa: FBT001
) -> None:
    assert gateway.holds("recurrence_due", "monthly", 31, ano, mes, dia) is esperado
