from dataclasses import dataclass, field


@dataclass(frozen=True, slots=True)
class AuthenticateUserInput:
    email: str
    password: str = field(repr=False)
