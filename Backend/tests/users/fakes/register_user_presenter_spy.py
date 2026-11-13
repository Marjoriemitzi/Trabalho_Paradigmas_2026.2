from app.users.application.dtos.register_user import RegisteredUser


class RegisterUserPresenterSpy:
    def __init__(self) -> None:
        self.registered: RegisteredUser | None = None
        self.email_taken: str | None = None
        self.weak_password: list[str] | None = None
        self.invalid_email: str | None = None

    def present_registered(self, user: RegisteredUser) -> None:
        self.registered = user

    def present_email_taken(self, email: str) -> None:
        self.email_taken = email

    def present_weak_password(self, reasons: list[str]) -> None:
        self.weak_password = reasons

    def present_invalid_email(self, email: str) -> None:
        self.invalid_email = email
