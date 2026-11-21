from datetime import date
from pathlib import Path

from app.finance.domain.value_objects.schedule import Schedule
from app.shared.infrastructure.prolog.gateway import PrologGateway


class PrologRecurrenceRules:
    def __init__(self, gateway: PrologGateway, rules_dir: Path) -> None:
        self._prolog = gateway
        self._prolog.consult(rules_dir / "finance" / "recurrence.pl")

    def is_due(self, schedule: Schedule, day: date) -> bool:
        return self._prolog.holds(
            "recurrence_due",
            schedule.frequency.value,
            schedule.day,
            day.year,
            day.month,
            day.day,
        )
