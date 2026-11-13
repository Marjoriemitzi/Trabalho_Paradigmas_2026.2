import uuid

import jwt

from app.users.application.ports.token_verifier import AuthenticatedUser
from app.users.domain.value_objects.role import Role
from app.users.domain.value_objects.user_id import UserId


class JwtTokenVerifier:
    def __init__(self, secret: str) -> None:
        self._secret = secret

    def verify(self, token: str) -> AuthenticatedUser | None:
        try:
            claims = jwt.decode(
                token,
                self._secret,
                algorithms=["HS256"],
                options={"require": ["sub", "role", "iat", "exp"]},
            )
            return AuthenticatedUser(
                id=UserId(uuid.UUID(claims["sub"])), role=Role(claims["role"])
            )
        except (jwt.InvalidTokenError, ValueError):
            return None
