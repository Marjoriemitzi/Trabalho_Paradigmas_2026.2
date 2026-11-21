from app.finance.application.dtos.create_account import AccountOutput


class RenameAccountPresenterSpy:
    def __init__(self) -> None:
        self.renamed: AccountOutput | None = None
        self.invalid: tuple[str, str] | None = None
        self.name_taken: str | None = None
        self.not_found = False

    def present_renamed(self, account: AccountOutput) -> None:
        self.renamed = account

    def present_invalid(self, field: str, problem: str) -> None:
        self.invalid = (field, problem)

    def present_name_taken(self, name: str) -> None:
        self.name_taken = name

    def present_not_found(self) -> None:
        self.not_found = True
