from collections.abc import Callable
from datetime import UTC, datetime

import jwt

from app.users.application.ports.token_verifier import AuthenticatedUser, TokenVerifier
from app.users.domain.entities.user import UserId


class JwtTokenVerifier(TokenVerifier):
    def __init__(
        self,
        secret: str,
        now: Callable[[], datetime] | None = None,
    ) -> None:
        self._secret = secret
        self._now = now or (lambda: datetime.now(UTC))

    def verify(self, token: str) -> AuthenticatedUser | None:
        try:
            payload = jwt.decode(token, self._secret, algorithms=["HS256"])
            exp_timestamp = payload.get("exp")
            return AuthenticatedUser(
                id=UserId(payload["sub"]),
                role=payload["role"],
                jti=payload.get("jti", ""),
                exp=datetime.fromtimestamp(exp_timestamp, tz=UTC)
                if exp_timestamp
                else self._now(),
            )
        except (jwt.InvalidTokenError, KeyError, ValueError):
            return None
