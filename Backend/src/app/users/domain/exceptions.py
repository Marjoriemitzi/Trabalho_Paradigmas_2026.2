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


class WeakPasswordError(DomainError):
    """
    A senha não cumpre a política. Quem decide é a porta PasswordPolicy.
    """

    def __init__(self, reasons: list[str]) -> None:
        super().__init__(f"Senha fraca: {', '.join(reasons)}")
        self.reasons = reasons


class EmailAlreadyRegisteredError(DomainError):
    def __init__(self, email: str) -> None:
        super().__init__(f"E-mail já cadastrado: {email}")
        self.email = email
