import hashlib
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Protocol

from app.users.application.ports.unit_of_work import UnitOfWork


@dataclass(frozen=True, slots=True)
class LogoutRequest:
    refresh_token: str


class LogoutOutputPort(Protocol):
    def present_success(self) -> None: ...


class LogoutInteractor:
    def __init__(self, uow: UnitOfWork, presenter: LogoutOutputPort) -> None:
        self._uow = uow
        self._presenter = presenter

    async def execute(self, request: LogoutRequest) -> None:
        token_hash = hashlib.sha256(request.refresh_token.encode()).hexdigest()
        now = datetime.now(UTC)
        stored = await self._uow.refresh_tokens.get_by_hash(token_hash)
        if stored and not stored["revoked_at"]:
            await self._uow.refresh_tokens.revoke_family(str(stored["family_id"]), now)
        await self._uow.refresh_tokens.delete_expired(now)
        await self._uow.commit()
        self._presenter.present_success()
