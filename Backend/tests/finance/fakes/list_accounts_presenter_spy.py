from app.finance.application.dtos.list_accounts import AccountSummary


class ListAccountsPresenterSpy:
    def __init__(self) -> None:
        self.accounts: tuple[AccountSummary, ...] | None = None

    def present_accounts(self, accounts: tuple[AccountSummary, ...]) -> None:
        self.accounts = accounts
