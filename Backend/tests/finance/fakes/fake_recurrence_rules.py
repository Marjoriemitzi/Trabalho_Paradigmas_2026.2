import calendar
from datetime import date

from app.finance.domain.value_objects.frequency import Frequency
from app.finance.domain.value_objects.schedule import Schedule


class FakeRecurrenceRules:
    """A mesma regra do recurrence.pl, em Python, para os testes sem Prolog."""

    def is_due(self, schedule: Schedule, day: date) -> bool:
        if schedule.frequency is Frequency.WEEKLY:
            return day.isoweekday() == schedule.day
        ultimo = calendar.monthrange(day.year, day.month)[1]
        return day.day == min(schedule.day, ultimo)
