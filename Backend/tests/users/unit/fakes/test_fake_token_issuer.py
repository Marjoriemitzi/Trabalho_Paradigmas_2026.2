from app.users.application.ports.token_issuer import TokenIssuer
from app.users.domain.entities.user import User
from app.users.domain.value_objects.email import Email
from app.users.domain.value_objects.password import PasswordHash
from tests.users.fakes.fake_token_issuer import FakeTokenIssuer


def test_gera_um_token_previsivel_para_o_usuario() -> None:
    user = User.register(Email("ana@acme.com"), PasswordHash("hash"))

    token = FakeTokenIssuer().issue(user)

    assert token.value == f"token-falso:{user.id.value}"
    assert token.expires_in == 1800


def test_fake_cumpre_a_porta() -> None:
    porta: TokenIssuer = FakeTokenIssuer()
    assert porta is not None
