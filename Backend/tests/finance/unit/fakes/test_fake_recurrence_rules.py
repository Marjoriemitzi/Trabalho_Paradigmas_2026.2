import pytest

from app.finance.domain.services.recurrence_rules import RecurrenceRules
from tests.finance.contracts.recurrence_rules_contract import RecurrenceRulesContract
from tests.finance.fakes.fake_recurrence_rules import FakeRecurrenceRules


class TestFakeRecurrenceRules(RecurrenceRulesContract):
    @pytest.fixture
    def rules(self) -> RecurrenceRules:
        return FakeRecurrenceRules()
