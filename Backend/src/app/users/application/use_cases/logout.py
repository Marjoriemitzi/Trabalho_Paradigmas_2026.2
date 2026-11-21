from dataclasses import dataclass
from typing import Protocol, override

from app.users.application.dtos.refresh_session import LogoutInput
from app.users.application.ports.clock import Clock
from app.users.application.ports.unit_of_work import UnitOfWork
from app.users.application.session import hash_refresh_token


class LogoutInputPort(Protocol):
    async def execute(self, data: LogoutInput) -> None: ...


class LogoutOutputPort(Protocol):
    def present_logged_out(self) -> None: ...


@dataclass(frozen=True, slots=True)
class LogoutInteractor(LogoutInputPort):
    uow: UnitOfWork
    clock: Clock
    presenter: LogoutOutputPort

    @override
    async def execute(self, data: LogoutInput) -> None:
        agora = self.clock.now()
        async with self.uow:
            token = await self.uow.refresh_tokens.get_by_hash(
                hash_refresh_token(data.refresh_token)
            )
            if token is not None:
                await self.uow.refresh_tokens.revoke_family(token.family_id, agora)
            atual = data.current
            if atual is not None and (token is None or token.user_id == atual.id):
                await self.uow.token_blocklist.add(
                    atual.jti, atual.id, atual.expires_at
                )
            await self.uow.token_blocklist.delete_expired(agora)
            await self.uow.commit()
        self.presenter.present_logged_out()
