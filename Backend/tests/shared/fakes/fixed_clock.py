from datetime import date, timedelta


class FixedClock:
    def __init__(self, day: date) -> None:
        self._day = day

    def today(self) -> date:
        return self._day

    def advance(self, days: int) -> None:
        self._day += timedelta(days=days)
