class FinanceDomainError(Exception): ...


class InvalidValueError(FinanceDomainError):
    def __init__(self, problem: str) -> None:
        super().__init__(problem)
        self.problem = problem
