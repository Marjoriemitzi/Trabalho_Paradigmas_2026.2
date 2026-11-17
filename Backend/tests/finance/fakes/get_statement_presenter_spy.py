from app.finance.application.dtos.get_statement import StatementOutput


class GetStatementPresenterSpy:
    def __init__(self) -> None:
        self.statement: StatementOutput | None = None
        self.invalid: tuple[str, str] | None = None
        self.account_not_found = False

    def present_statement(self, statement: StatementOutput) -> None:
        self.statement = statement

    def present_invalid(self, field: str, problem: str) -> None:
        self.invalid = (field, problem)

    def present_account_not_found(self) -> None:
        self.account_not_found = True
