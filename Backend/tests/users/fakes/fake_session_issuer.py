from datetime import timedelta

from app.users.application.session import SessionIssuer
from tests.users.fakes.fake_clock import FakeClock
from tests.users.fakes.fake_refresh_token_generator import FakeRefreshTokenGenerator
from tests.users.fakes.fake_token_issuer import FakeTokenIssuer


def fake_session_issuer(clock: FakeClock | None = None) -> SessionIssuer:
    return SessionIssuer(
        tokens=FakeTokenIssuer(),
        generator=FakeRefreshTokenGenerator(),
        clock=clock or FakeClock(),
        refresh_ttl=timedelta(days=30),
    )
