from collections.abc import Callable
from datetime import UTC, date, datetime
from zoneinfo import ZoneInfo


def _agora_utc() -> datetime:
    return datetime.now(UTC)


class ZoneInfoClock:
    def __init__(self, tz: ZoneInfo, now: Callable[[], datetime] = _agora_utc) -> None:
        self._tz = tz
        self._now = now

    def today(self) -> date:
        return self._now().astimezone(self._tz).date()
