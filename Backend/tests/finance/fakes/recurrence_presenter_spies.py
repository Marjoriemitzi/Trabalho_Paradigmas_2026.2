from app.finance.application.dtos.recurrences import RecurrenceOutput


class CreateRecurrencePresenterSpy:
    def __init__(self) -> None:
        self.created: RecurrenceOutput | None = None
        self.invalid: tuple[str, str] | None = None

    def present_created(self, recurrence: RecurrenceOutput) -> None:
        self.created = recurrence

    def present_invalid(self, field: str, problem: str) -> None:
        self.invalid = (field, problem)


class UpdateRecurrencePresenterSpy:
    def __init__(self) -> None:
        self.updated: RecurrenceOutput | None = None
        self.invalid: tuple[str, str] | None = None
        self.not_found = False

    def present_updated(self, recurrence: RecurrenceOutput) -> None:
        self.updated = recurrence

    def present_invalid(self, field: str, problem: str) -> None:
        self.invalid = (field, problem)

    def present_not_found(self) -> None:
        self.not_found = True


class DeleteRecurrencePresenterSpy:
    def __init__(self) -> None:
        self.deleted = False
        self.not_found = False

    def present_deleted(self) -> None:
        self.deleted = True

    def present_not_found(self) -> None:
        self.not_found = True


class ListRecurrencesPresenterSpy:
    def __init__(self) -> None:
        self.listed: list[RecurrenceOutput] | None = None

    def present_listed(self, recurrences: list[RecurrenceOutput]) -> None:
        self.listed = recurrences
