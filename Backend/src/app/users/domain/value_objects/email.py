"""Email: value object imutável que só existe se for válido."""

import re
from dataclasses import dataclass

from app.users.domain.exceptions import InvalidEmailError

_EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


@dataclass(frozen=True, slots=True)
class Email:
    value: str

    def __post_init__(self) -> None:
        normalized = self.value.strip().lower()
        if not _EMAIL_RE.fullmatch(normalized):
            raise InvalidEmailError(self.value)
        object.__setattr__(self, "value", normalized)
