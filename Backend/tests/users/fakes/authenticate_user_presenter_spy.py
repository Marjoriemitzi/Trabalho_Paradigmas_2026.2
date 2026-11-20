from app.users.application.session import Session


class AuthenticateUserPresenterSpy:
    def __init__(self) -> None:
        self.session: Session | None = None
        self.invalid_credentials = False
        self.retry_after: int | None = None

    def present_authenticated(self, session: Session) -> None:
        self.session = session

    def present_invalid_credentials(self) -> None:
        self.invalid_credentials = True

    def present_too_many_attempts(self, retry_after: int) -> None:
        self.retry_after = retry_after
