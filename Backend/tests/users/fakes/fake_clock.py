from datetime import UTC, datetime, timedelta


class FakeClock:
    def __init__(self) -> None:
        self.current = datetime(2026, 11, 20, 12, 0, tzinfo=UTC)

    def now(self) -> datetime:
        return self.current

    def advance(self, delta: timedelta) -> None:
        self.current += delta
