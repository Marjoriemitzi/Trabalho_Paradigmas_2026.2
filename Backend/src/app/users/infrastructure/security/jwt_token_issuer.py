from collections.abc import Callable
from datetime import UTC, datetime, timedelta

import jwt

from app.users.application.ports.token_issuer import AccessToken
from app.users.domain.entities.user import User


def _agora() -> datetime:
    return datetime.now(UTC)


class JwtTokenIssuer:
    def __init__(
        self,
        secret: str,
        expires_in: timedelta,
        now: Callable[[], datetime] = _agora,
    ) -> None:
        self._secret = secret
        self._expires_in = expires_in
        self._now = now

    def issue(self, user: User) -> AccessToken:
        agora = self._now()
        claims = {
            "sub": str(user.id.value),
            "role": user.role.value,
            "iat": agora,
            "exp": agora + self._expires_in,
        }
        token = jwt.encode(claims, self._secret, algorithm="HS256")
        return AccessToken(token, int(self._expires_in.total_seconds()))
