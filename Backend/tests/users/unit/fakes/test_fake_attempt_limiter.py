import pytest

from app.users.application.ports.attempt_limiter import AttemptLimiter
from tests.users.contracts.attempt_limiter_contract import AttemptLimiterContract
from tests.users.fakes.fake_attempt_limiter import FakeAttemptLimiter


class TestFakeAttemptLimiter(AttemptLimiterContract):
    @pytest.fixture
    def limiter(self) -> AttemptLimiter:
        return FakeAttemptLimiter()
