from app.finance.application.dtos.transfers import TransferListOutput, TransferOutput


class CreateTransferPresenterSpy:
    def __init__(self) -> None:
        self.created: TransferOutput | None = None
        self.invalid: tuple[str, str] | None = None

    def present_created(self, transfer: TransferOutput) -> None:
        self.created = transfer

    def present_invalid(self, field: str, problem: str) -> None:
        self.invalid = (field, problem)


class DeleteTransferPresenterSpy:
    def __init__(self) -> None:
        self.deleted = False
        self.not_found = False

    def present_deleted(self) -> None:
        self.deleted = True

    def present_not_found(self) -> None:
        self.not_found = True


class UpdateTransferPresenterSpy:
    def __init__(self) -> None:
        self.updated: TransferOutput | None = None
        self.invalid: tuple[str, str] | None = None
        self.not_found = False

    def present_updated(self, transfer: TransferOutput) -> None:
        self.updated = transfer

    def present_invalid(self, field: str, problem: str) -> None:
        self.invalid = (field, problem)

    def present_not_found(self) -> None:
        self.not_found = True


class ListTransfersPresenterSpy:
    def __init__(self) -> None:
        self.listed: TransferListOutput | None = None
        self.invalid: tuple[str, str] | None = None

    def present_listed(self, listing: TransferListOutput) -> None:
        self.listed = listing

    def present_invalid(self, field: str, problem: str) -> None:
        self.invalid = (field, problem)
