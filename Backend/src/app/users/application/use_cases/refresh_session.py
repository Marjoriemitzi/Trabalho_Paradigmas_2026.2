from dataclasses import dataclass
from typing import Protocol, override

from app.users.application.dtos.refresh_session import RefreshSessionInput
from app.users.application.ports.clock import Clock
from app.users.application.ports.unit_of_work import UnitOfWork
from app.users.application.session import Session, SessionIssuer, hash_refresh_token


class RefreshSessionInputPort(Protocol):
    async def execute(self, data: RefreshSessionInput) -> None: ...


class RefreshSessionOutputPort(Protocol):
    def present_refreshed(self, session: Session) -> None: ...

    def present_invalid_refresh_token(self) -> None: ...


@dataclass(frozen=True, slots=True)
class RefreshSessionInteractor(RefreshSessionInputPort):
    uow: UnitOfWork
    issuer: SessionIssuer
    clock: Clock
    presenter: RefreshSessionOutputPort

    @override
    async def execute(self, data: RefreshSessionInput) -> None:
        session = await self._rotate(data.refresh_token)
        if session is None:
            self.presenter.present_invalid_refresh_token()
            return
        self.presenter.present_refreshed(session)

    async def _rotate(self, refresh_token: str) -> Session | None:
        agora = self.clock.now()
        async with self.uow:
            token = await self.uow.refresh_tokens.get_by_hash(
                hash_refresh_token(refresh_token)
            )
            if token is None or token.revoked_at is not None:
                return None
            if token.is_expired(agora):
                return None
            if token.used_at is not None or not await self.uow.refresh_tokens.mark_used(
                token.id, agora
            ):
                await self.uow.refresh_tokens.revoke_family(token.family_id, agora)
                await self.uow.commit()
                return None
            user = await self.uow.users.get_by_id(token.user_id)
            if user is None:
                return None
            session = await self.issuer.issue(self.uow, user, token.family_id)
            await self.uow.commit()
            return session
