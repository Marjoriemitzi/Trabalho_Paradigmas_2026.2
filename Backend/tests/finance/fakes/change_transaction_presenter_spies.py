from app.finance.application.dtos.record_transaction import RecordedTransaction


class UpdateTransactionPresenterSpy:
    def __init__(self) -> None:
        self.updated: RecordedTransaction | None = None
        self.invalid: tuple[str, str] | None = None
        self.not_found = False

    def present_updated(self, transaction: RecordedTransaction) -> None:
        self.updated = transaction

    def present_invalid(self, field: str, problem: str) -> None:
        self.invalid = (field, problem)

    def present_not_found(self) -> None:
        self.not_found = True


class DeleteTransactionPresenterSpy:
    def __init__(self) -> None:
        self.deleted = False
        self.not_found = False

    def present_deleted(self) -> None:
        self.deleted = True

    def present_not_found(self) -> None:
        self.not_found = True
