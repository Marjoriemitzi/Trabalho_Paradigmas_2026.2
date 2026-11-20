from dataclasses import dataclass, field


@dataclass(frozen=True, slots=True)
class RefreshSessionInput:
    refresh_token: str = field(repr=False)


@dataclass(frozen=True, slots=True)
class LogoutInput:
    refresh_token: str = field(repr=False)
