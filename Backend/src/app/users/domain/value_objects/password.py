from dataclasses import dataclass, field


@dataclass(frozen=True, slots=True)
class RawPassword:
    _secret: str = field(repr=False)

    def __post_init__(self) -> None:
        if self._secret == "":
            raise ValueError("A senha não pode ser vazia.")
        if "\x00" in self._secret:
            raise ValueError("A senha não pode conter byte NUL.")

    def reveal(self) -> str:
        return self._secret


@dataclass(frozen=True, slots=True)
class PasswordHash:
    value: str = field(repr=False)

    def __post_init__(self) -> None:
        if self.value == "":
            raise ValueError("O hash não pode ser vazio.")
