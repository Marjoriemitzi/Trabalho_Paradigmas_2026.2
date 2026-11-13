from app.users.application.ports.token_verifier import TokenVerifier
from app.users.domain.entities.user import User
from app.users.domain.value_objects.email import Email
from app.users.domain.value_objects.password import PasswordHash
from app.users.domain.value_objects.role import Role
from tests.users.fakes.fake_token_issuer import FakeTokenIssuer
from tests.users.fakes.fake_token_verifier import FakeTokenVerifier


def test_aceita_o_token_do_emissor_falso() -> None:
    user = User.register(Email("ana@acme.com"), PasswordHash("hash"))
    token = FakeTokenIssuer().issue(user)

    autenticado = FakeTokenVerifier().verify(token.value)

    assert autenticado is not None
    assert autenticado.id == user.id
    assert autenticado.role is Role.USER


def test_recusa_qualquer_outro_texto() -> None:
    assert FakeTokenVerifier().verify("qualquer-coisa") is None


def test_fake_cumpre_a_porta() -> None:
    porta: TokenVerifier = FakeTokenVerifier()
    assert porta is not None
