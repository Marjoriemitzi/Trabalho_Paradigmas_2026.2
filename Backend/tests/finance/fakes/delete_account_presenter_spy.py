class DeleteAccountPresenterSpy:
    def __init__(self) -> None:
        self.deleted = False
        self.in_use = False
        self.not_found = False

    def present_deleted(self) -> None:
        self.deleted = True

    def present_in_use(self) -> None:
        self.in_use = True

    def present_not_found(self) -> None:
        self.not_found = True
