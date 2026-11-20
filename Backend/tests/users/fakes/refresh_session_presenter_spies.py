from app.users.application.session import Session


class RefreshSessionPresenterSpy:
    def __init__(self) -> None:
        self.session: Session | None = None
        self.invalid = False

    def present_refreshed(self, session: Session) -> None:
        self.session = session

    def present_invalid_refresh_token(self) -> None:
        self.invalid = True


class LogoutPresenterSpy:
    def __init__(self) -> None:
        self.logged_out = False

    def present_logged_out(self) -> None:
        self.logged_out = True
