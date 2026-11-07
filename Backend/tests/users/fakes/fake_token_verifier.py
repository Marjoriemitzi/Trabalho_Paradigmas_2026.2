import uuid

from app.users.application.ports.token_verifier import AuthenticatedUser
from app.users.domain.value_objects.role import Role
from app.users.domain.value_objects.user_id import UserId

PREFIXO = "token-falso:"


class FakeTokenVerifier:
    def verify(self, token: str) -> AuthenticatedUser | None:
        if not token.startswith(PREFIXO):
            return None
        return AuthenticatedUser(
            id=UserId(uuid.UUID(token.removeprefix(PREFIXO))), role=Role.USER
        )
