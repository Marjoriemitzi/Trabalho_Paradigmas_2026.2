import uuid
from datetime import UTC, datetime, timedelta

from app.users.application.ports.token_verifier import AuthenticatedUser
from app.users.domain.value_objects.role import Role
from app.users.domain.value_objects.user_id import UserId


def autenticado(
    user_id: UserId,
    role: Role = Role.USER,
    jti: uuid.UUID | None = None,
    expires_at: datetime | None = None,
) -> AuthenticatedUser:
    return AuthenticatedUser(
        id=user_id,
        role=role,
        jti=jti or uuid.uuid4(),
        expires_at=expires_at or datetime.now(UTC) + timedelta(minutes=15),
    )
