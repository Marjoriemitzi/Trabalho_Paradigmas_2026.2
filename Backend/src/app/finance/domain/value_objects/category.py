import re
from dataclasses import dataclass

from app.finance.domain.exceptions import InvalidValueError

_FORMATO = re.compile(r"[a-z][a-z0-9_]{0,39}")


@dataclass(frozen=True, slots=True)
class Category:
    name: str

    def __post_init__(self) -> None:
        normalizado = self.name.strip().lower()
        if not _FORMATO.fullmatch(normalizado):
            raise InvalidValueError("invalid_format")
        object.__setattr__(self, "name", normalizado)
