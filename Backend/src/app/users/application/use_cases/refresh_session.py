import hashlib
import secrets
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from typing import Protocol

from app.users.application.ports.token_issuer import TokenIssuer
from app.users.application.ports.unit_of_work import UnitOfWork


@dataclass(frozen=True, slots=True)
class RefreshSessionRequest:
    refresh_token: str


class RefreshSessionOutputPort(Protocol):
    def present_success(
        self,
        access_token: str,
        expires_in: int,
        refresh_token: str,
        refresh_expires_in: int,
    ) -> None: ...
    def present_invalid_refresh_token(self) -> None: ...


class RefreshSessionInteractor:
    def __init__(
        self,
        uow: UnitOfWork,
        token_issuer: TokenIssuer,
        access_minutes: int,
        refresh_days: int,
        presenter: RefreshSessionOutputPort,
    ) -> None:
        self._uow = uow
        self._issuer = token_issuer
        self._access = access_minutes
        self._refresh = refresh_days
        self._presenter = presenter

    async def execute(self, request: RefreshSessionRequest) -> None:
        token_hash = hashlib.sha256(request.refresh_token.encode()).hexdigest()
        now = datetime.now(UTC)
        stored = await self._uow.refresh_tokens.get_by_hash(token_hash)
        if not stored or stored["revoked_at"] or stored["expires_at"] < now:
            self._presenter.present_invalid_refresh_token()
            return
        if stored["used_at"]:
            await self._uow.refresh_tokens.revoke_family(stored["family_id"], now)
            await self._uow.commit()
            self._presenter.present_invalid_refresh_token()
            return
        await self._uow.refresh_tokens.mark_used(stored["id"], now)
        user = await self._uow.users.get_by_id(stored["user_id"])
        if not user:
            self._presenter.present_invalid_refresh_token()
            return
        access_token = self._issuer.issue(user.id, user.role)
        access_exp = self._access * 60
        new_refresh = secrets.token_urlsafe(32)
        new_hash = hashlib.sha256(new_refresh.encode()).hexdigest()
        new_expires_at = now + timedelta(days=self._refresh)
        await self._uow.refresh_tokens.add(
            user.id.value, stored["family_id"], new_hash, new_expires_at
        )
        await self._uow.refresh_tokens.delete_expired(now)
        await self._uow.commit()
        self._presenter.present_success(
            access_token, access_exp, new_refresh, self._refresh * 86400
        )
