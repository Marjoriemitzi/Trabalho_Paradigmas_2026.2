from dataclasses import dataclass, field

from app.users.application.ports.token_verifier import AuthenticatedUser


@dataclass(frozen=True, slots=True)
class RefreshSessionInput:
    refresh_token: str = field(repr=False)


@dataclass(frozen=True, slots=True)
class LogoutInput:
    refresh_token: str = field(repr=False)
    current: AuthenticatedUser | None = None
