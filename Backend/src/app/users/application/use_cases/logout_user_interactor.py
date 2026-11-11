from datetime import UTC, datetime

import jwt

from app.users.application.ports.token_blocklist_repository import (
    TokenBlocklistRepository,
)


class LogoutUserInteractor:
    def __init__(self, blocklist_repo: TokenBlocklistRepository) -> None:
        self._blocklist_repo = blocklist_repo

    async def execute(self, token: str) -> None:
        try:
            payload = jwt.decode(token, options={"verify_signature": False})
            exp_timestamp = payload.get("exp")
            if exp_timestamp:
                expires_at = datetime.fromtimestamp(exp_timestamp, tz=UTC)
                await self._blocklist_repo.add(token, expires_at)
        except jwt.DecodeError:
            pass
