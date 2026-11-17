from app.finance.application.dtos.record_transaction import RecordedTransaction


class RecordTransactionPresenterSpy:
    def __init__(self) -> None:
        self.recorded: RecordedTransaction | None = None
        self.invalid: tuple[str, str] | None = None

    def present_recorded(self, transaction: RecordedTransaction) -> None:
        self.recorded = transaction

    def present_invalid(self, field: str, problem: str) -> None:
        self.invalid = (field, problem)
