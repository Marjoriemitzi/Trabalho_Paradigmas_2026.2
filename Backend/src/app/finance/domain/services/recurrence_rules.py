from datetime import date
from typing import Protocol

from app.finance.domain.value_objects.schedule import Schedule


class RecurrenceRules(Protocol):
    def is_due(self, schedule: Schedule, day: date) -> bool: ...
