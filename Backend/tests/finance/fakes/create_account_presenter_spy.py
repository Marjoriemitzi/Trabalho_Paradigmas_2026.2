from app.finance.application.dtos.create_account import AccountOutput


class CreateAccountPresenterSpy:
    def __init__(self) -> None:
        self.created: AccountOutput | None = None
        self.invalid: tuple[str, str] | None = None
        self.name_taken: str | None = None

    def present_created(self, account: AccountOutput) -> None:
        self.created = account

    def present_invalid(self, field: str, problem: str) -> None:
        self.invalid = (field, problem)

    def present_name_taken(self, name: str) -> None:
        self.name_taken = name
