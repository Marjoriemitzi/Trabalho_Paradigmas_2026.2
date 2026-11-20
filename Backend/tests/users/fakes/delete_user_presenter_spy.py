class DeleteUserPresenterSpy:
    def __init__(self) -> None:
        self.deleted = False
        self.invalid_current_password = False
        self.user_not_found = False

    def present_deleted(self) -> None:
        self.deleted = True

    def present_invalid_current_password(self) -> None:
        self.invalid_current_password = True

    def present_user_not_found(self) -> None:
        self.user_not_found = True
