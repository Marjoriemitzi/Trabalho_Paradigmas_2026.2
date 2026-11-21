from collections.abc import Sequence

from app.users.application.dtos.register_user import RegisteredUser


class RegisterUserPresenterSpy:
    def __init__(self) -> None:
        self.registered: RegisteredUser | None = None
        self.email_taken: str | None = None
        self.weak_password: Sequence[str] | None = None
        self.invalid_email: str | None = None
        self.retry_after: int | None = None

    def present_registered(self, user: RegisteredUser) -> None:
        self.registered = user

    def present_email_taken(self, email: str) -> None:
        self.email_taken = email

    def present_weak_password(self, reasons: Sequence[str]) -> None:
        self.weak_password = reasons

    def present_invalid_email(self, email: str) -> None:
        self.invalid_email = email

    def present_too_many_attempts(self, retry_after: int) -> None:
        self.retry_after = retry_after
