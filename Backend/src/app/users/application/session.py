import hashlib
import uuid
from dataclasses import dataclass, field
from datetime import timedelta

from app.users.application.ports.clock import Clock
from app.users.application.ports.refresh_token_generator import RefreshTokenGenerator
from app.users.application.ports.token_issuer import AccessToken, TokenIssuer
from app.users.application.ports.unit_of_work import UnitOfWork
from app.users.domain.entities.refresh_token import RefreshToken
from app.users.domain.entities.user import User

EXPIRED_RETENTION = timedelta(days=7)


@dataclass(frozen=True, slots=True)
class Session:
    access_token: AccessToken
    refresh_token: str = field(repr=False)
    refresh_expires_in: int


def hash_refresh_token(token: str) -> str:
    return hashlib.sha256(token.encode()).hexdigest()


@dataclass(frozen=True, slots=True)
class SessionIssuer:
    tokens: TokenIssuer
    generator: RefreshTokenGenerator
    clock: Clock
    refresh_ttl: timedelta

    async def issue(
        self, uow: UnitOfWork, user: User, family_id: uuid.UUID | None = None
    ) -> Session:
        """Emite o par de tokens. Quem chama dá o commit."""
        agora = self.clock.now()
        refresh = self.generator.generate()
        await uow.refresh_tokens.add(
            RefreshToken.issue(
                user_id=user.id,
                family_id=family_id or uuid.uuid4(),
                token_hash=hash_refresh_token(refresh),
                expires_at=agora + self.refresh_ttl,
            )
        )
        await uow.refresh_tokens.delete_expired_before(agora - EXPIRED_RETENTION)
        return Session(
            access_token=self.tokens.issue(user),
            refresh_token=refresh,
            refresh_expires_in=int(self.refresh_ttl.total_seconds()),
        )
