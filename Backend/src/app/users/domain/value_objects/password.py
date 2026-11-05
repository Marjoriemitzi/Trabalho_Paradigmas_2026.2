"""
Value objects de senha.

RawPassword carrega o texto puro só até ele virar hash.
A força da senha NÃO é decidida aqui:
    é regra de negócio, delegada ao Prolog pela porta PasswordPolicy.
"""

from dataclasses import dataclass, field


@dataclass(frozen=True, slots=True)
class RawPassword:
    _secret: str = field(repr=False)

    def __post_init__(self) -> None:
        if not self._secret:
            raise ValueError("A senha não pode ser vazia.")

    def reveal(self) -> str:
        """
        Devolve o texto puro.
        Só quem vai gerar o hash deve chamar.
        """
        return self._secret


@dataclass(frozen=True, slots=True)
class PasswordHash:
    """
    Hash da senha, o único formato que pode ser persistido.
    """

    value: str = field(repr=False)

    def __post_init__(self) -> None:
        if not self.value:
            raise ValueError("O hash não pode ser vazio.")
