from collections.abc import Sequence


class ChangePasswordPresenterSpy:
    def __init__(self) -> None:
        self.changed = False
        self.invalid_current_password = False
        self.weak_password: Sequence[str] | None = None
        self.user_not_found = False

    def present_changed(self) -> None:
        self.changed = True

    def present_invalid_current_password(self) -> None:
        self.invalid_current_password = True

    def present_weak_password(self, reasons: Sequence[str]) -> None:
        self.weak_password = reasons

    def present_user_not_found(self) -> None:
        self.user_not_found = True
