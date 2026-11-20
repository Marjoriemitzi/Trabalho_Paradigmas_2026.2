import uuid
from datetime import UTC, datetime

from app.users.application.ports.token_verifier import AuthenticatedUser
from app.users.domain.value_objects.role import Role
from app.users.domain.value_objects.user_id import UserId

PREFIXO = "token-falso:"


class FakeTokenVerifier:
    """O jti do token falso é o próprio id do usuário, para os testes o bloquearem."""

    def verify(self, token: str) -> AuthenticatedUser | None:
        if not token.startswith(PREFIXO):
            return None
        try:
            user_id = uuid.UUID(token.removeprefix(PREFIXO))
        except ValueError:
            return None
        return AuthenticatedUser(
            id=UserId(user_id),
            role=Role.USER,
            jti=user_id,
            expires_at=datetime(2100, 1, 1, tzinfo=UTC),
        )
