from dataclasses import dataclass

from app.finance.domain.exceptions import InvalidValueError

# Teto em centavos (~R$ 100 bilhões): bem abaixo do int64 do PostgreSQL e do Prolog,
# deixando folga para somas de muitos valores sem estourar 64 bits.
MAX_CENTS = 9_999_999_999_999


@dataclass(frozen=True, slots=True)
class Money:
    cents: int

    def __post_init__(self) -> None:
        valor: object = self.cents
        if isinstance(valor, bool) or not isinstance(valor, int):
            raise TypeError("Centavos devem ser um inteiro.")
        if self.cents <= 0:
            raise InvalidValueError("not_positive")
        if self.cents > MAX_CENTS:
            raise InvalidValueError("too_large")
