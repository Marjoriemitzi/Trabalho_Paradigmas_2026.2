import uuid
from dataclasses import replace
from datetime import datetime

from app.users.domain.entities.refresh_token import RefreshToken


class FakeRefreshTokenRepository:
    def __init__(self) -> None:
        self.stored: dict[uuid.UUID, RefreshToken] = {}

    async def add(self, token: RefreshToken) -> None:
        self.stored[token.id] = token

    async def get_by_hash(self, token_hash: str) -> RefreshToken | None:
        return next(
            (t for t in self.stored.values() if t.token_hash == token_hash), None
        )

    async def mark_used(self, token_id: uuid.UUID, now: datetime) -> bool:
        token = self.stored.get(token_id)
        if token is None or token.used_at is not None or token.revoked_at is not None:
            return False
        self.stored[token_id] = replace(token, used_at=now)
        return True

    async def revoke_family(self, family_id: uuid.UUID, now: datetime) -> None:
        for token_id, token in list(self.stored.items()):
            if token.family_id == family_id and token.revoked_at is None:
                self.stored[token_id] = replace(token, revoked_at=now)

    async def delete_expired_before(self, limit: datetime) -> None:
        self.stored = {k: t for k, t in self.stored.items() if t.expires_at >= limit}
