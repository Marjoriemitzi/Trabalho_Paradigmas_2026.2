from dataclasses import dataclass, field


@dataclass(frozen=True, slots=True)
class RawPassword:
    _secret: str = field(repr=False)

    def __post_init__(self) -> None:
        if not self._secret:
            raise ValueError("A senha não pode ser vazia.")

    def reveal(self) -> str:
        return self._secret


@dataclass(frozen=True, slots=True)
class PasswordHash:
    value: str = field(repr=False)

    def __post_init__(self) -> None:
        if not self.value:
            raise ValueError("O hash não pode ser vazio.")
