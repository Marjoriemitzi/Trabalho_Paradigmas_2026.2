import uuid
from collections.abc import Callable
from datetime import UTC, datetime, timedelta

import jwt

from app.users.application.ports.token_issuer import AccessToken, TokenIssuer
from app.users.domain.entities.user import User


class JwtTokenIssuer(TokenIssuer):
    def __init__(
        self,
        secret: str,
        expires_in: timedelta,
        now: Callable[[], datetime] | None = None,
    ) -> None:
        self._secret = secret
        self._expires_in = expires_in
        self._now = now or (lambda: datetime.now(UTC))

    def issue(self, user: User) -> AccessToken:
        current_time = self._now()
        payload = {
            "sub": str(user.id),
            "role": user.role,
            "jti": str(uuid.uuid4()),
            "iat": current_time,
            "exp": current_time + self._expires_in,
        }
        token = jwt.encode(payload, self._secret, algorithm="HS256")
        return AccessToken(
            value=token, expires_in=int(self._expires_in.total_seconds())
        )
