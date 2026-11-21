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
