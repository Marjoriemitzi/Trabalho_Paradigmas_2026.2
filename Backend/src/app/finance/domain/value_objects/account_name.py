from dataclasses import dataclass

from app.finance.domain.exceptions import InvalidValueError

MAX_LENGTH = 60


@dataclass(frozen=True, slots=True)
class AccountName:
    text: str

    def __post_init__(self) -> None:
        limpo = self.text.strip()
        if not limpo:
            raise InvalidValueError("blank")
        if len(limpo) > MAX_LENGTH:
            raise InvalidValueError("too_long")
        object.__setattr__(self, "text", limpo)

    @property
    def key(self) -> str:
        return self.text.lower()
