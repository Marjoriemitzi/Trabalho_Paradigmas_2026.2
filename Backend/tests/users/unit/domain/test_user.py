from app.users.domain.entities.user import User
from app.users.domain.value_objects.email import Email
from app.users.domain.value_objects.password import PasswordHash
from app.users.domain.value_objects.role import Role

EMAIL = Email("ana@acme.com")
HASH = PasswordHash("$argon2id$v=19$m=65536,t=3,p=4$c2FsdA$aGFzaA")


def test_register_guarda_email_e_hash() -> None:
    user = User.register(EMAIL, HASH)
    assert user.email == EMAIL
    assert user.password_hash == HASH


def test_cada_cadastro_recebe_uma_identidade_nova() -> None:
    assert User.register(EMAIL, HASH).id != User.register(EMAIL, HASH).id


def test_mesma_identidade_e_o_mesmo_usuario_mesmo_com_dados_diferentes() -> None:
    user = User.register(EMAIL, HASH)
    mesmo_usuario_depois = User(
        id=user.id, email=Email("ana@novo.com"), password_hash=HASH
    )
    assert user == mesmo_usuario_depois


def test_pode_ser_usado_em_conjuntos() -> None:
    user = User.register(EMAIL, HASH)
    copia = User(id=user.id, email=user.email, password_hash=user.password_hash)
    assert len({user, copia}) == 1


def test_usuario_novo_comeca_como_usuario_comum() -> None:
    assert User.register(EMAIL, HASH).role is Role.USER
