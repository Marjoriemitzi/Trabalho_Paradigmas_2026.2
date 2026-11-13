from dataclasses import dataclass

from app.finance.domain.exceptions import InvalidValueError

MAX_LENGTH = 200


@dataclass(frozen=True, slots=True)
class Description:
    text: str

    def __post_init__(self) -> None:
        limpo = self.text.strip()
        if not limpo:
            raise InvalidValueError("blank")
        if len(limpo) > MAX_LENGTH:
            raise InvalidValueError("too_long")
        object.__setattr__(self, "text", limpo)
