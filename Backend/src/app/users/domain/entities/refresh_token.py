import uuid
from dataclasses import dataclass
from datetime import datetime
from typing import Self

from app.users.domain.value_objects.user_id import UserId


@dataclass(frozen=True, slots=True)
class RefreshToken:
    id: uuid.UUID
    user_id: UserId
    family_id: uuid.UUID
    token_hash: str
    expires_at: datetime
    used_at: datetime | None = None
    revoked_at: datetime | None = None

    @classmethod
    def issue(
        cls,
        user_id: UserId,
        family_id: uuid.UUID,
        token_hash: str,
        expires_at: datetime,
    ) -> Self:
        return cls(
            id=uuid.uuid4(),
            user_id=user_id,
            family_id=family_id,
            token_hash=token_hash,
            expires_at=expires_at,
        )

    def is_expired(self, now: datetime) -> bool:
        return self.expires_at <= now
