import uuid
from datetime import datetime

from app.users.domain.value_objects.user_id import UserId


class FakeTokenBlocklist:
    def __init__(self) -> None:
        self.stored: dict[uuid.UUID, tuple[UserId, datetime]] = {}

    async def add(self, jti: uuid.UUID, user_id: UserId, expires_at: datetime) -> None:
        self.stored.setdefault(jti, (user_id, expires_at))

    async def contains(self, jti: uuid.UUID) -> bool:
        return jti in self.stored

    async def delete_expired(self, now: datetime) -> None:
        self.stored = {j: v for j, v in self.stored.items() if v[1] >= now}
