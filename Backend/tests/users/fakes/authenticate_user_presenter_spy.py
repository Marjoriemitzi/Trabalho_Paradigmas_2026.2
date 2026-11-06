from app.users.application.ports.token_issuer import AccessToken


class AuthenticateUserPresenterSpy:
    def __init__(self) -> None:
        self.token: AccessToken | None = None
        self.invalid_credentials = False

    def present_authenticated(self, token: AccessToken) -> None:
        self.token = token

    def present_invalid_credentials(self) -> None:
        self.invalid_credentials = True
