"""
Erros de regra de negócio do contexto de usuários. Nenhum deles conhece HTTP.
"""


class DomainError(Exception):
    """
    Base dos erros de domínio deste contexto.
    """


class InvalidEmailError(DomainError):
    def __init__(self, value: str) -> None:
        super().__init__(f"E-mail inválido: {value!r}")
        self.value = value
