from app.users.application.attempts import AttemptGuard, AttemptLimits
from tests.users.fakes.fake_attempt_limiter import FakeAttemptLimiter
from tests.users.fakes.fake_clock import FakeClock


def fake_attempt_guard(
    clock: FakeClock | None = None,
    limits: AttemptLimits | None = None,
    limiter: FakeAttemptLimiter | None = None,
) -> AttemptGuard:
    return AttemptGuard(
        limiter=limiter or FakeAttemptLimiter(),
        clock=clock or FakeClock(),
        limits=limits or AttemptLimits(),
    )
