from app.users.application.ports.token_issuer import AccessToken
from app.users.domain.entities.user import User


class FakeTokenIssuer:
    def issue(self, user: User) -> AccessToken:
        return AccessToken(f"token-falso:{user.id.value}", expires_in=1800)
