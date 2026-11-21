from dataclasses import dataclass

from app.finance.domain.exceptions import InvalidValueError


@dataclass(frozen=True, slots=True)
class Money:
    cents: int

    def __post_init__(self) -> None:
        valor: object = self.cents
        if isinstance(valor, bool) or not isinstance(valor, int):
            raise TypeError("Centavos devem ser um inteiro.")
        if self.cents <= 0:
            raise InvalidValueError("not_positive")
