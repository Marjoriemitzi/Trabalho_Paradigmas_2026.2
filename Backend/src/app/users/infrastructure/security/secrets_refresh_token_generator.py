import secrets


class SecretsRefreshTokenGenerator:
    def generate(self) -> str:
        return secrets.token_urlsafe(32)
