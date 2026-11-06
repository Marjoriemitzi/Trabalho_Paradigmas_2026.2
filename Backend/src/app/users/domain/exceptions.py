class DomainError(Exception): ...


class InvalidEmailError(DomainError):
    def __init__(self, value: str) -> None:
        super().__init__(f"E-mail inválido: {value!r}")
        self.value = value


class WeakPasswordError(DomainError):
    def __init__(self, reasons: list[str]) -> None:
        super().__init__(f"Senha fraca: {', '.join(reasons)}")
        self.reasons = reasons


class EmailAlreadyRegisteredError(DomainError):
    def __init__(self, email: str) -> None:
        super().__init__(f"E-mail já cadastrado: {email}")
        self.email = email
