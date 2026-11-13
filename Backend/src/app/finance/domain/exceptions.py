class FinanceDomainError(Exception):
    pass


class InvalidValueError(FinanceDomainError):
    def __init__(self, problem: str) -> None:
        super().__init__(problem)
        self.problem = problem


class AccountNameTakenError(FinanceDomainError):
    def __init__(self, name: str) -> None:
        super().__init__(f"Já existe uma conta chamada {name!r}")
        self.name = name
