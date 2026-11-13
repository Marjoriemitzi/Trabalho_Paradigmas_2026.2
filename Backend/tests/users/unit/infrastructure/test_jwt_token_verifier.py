from datetime import UTC, datetime, timedelta

import jwt

from app.users.application.ports.token_verifier import TokenVerifier
from app.users.domain.entities.user import User
from app.users.domain.value_objects.email import Email
from app.users.domain.value_objects.password import PasswordHash
from app.users.domain.value_objects.role import Role
from app.users.infrastructure.security.jwt_token_issuer import JwtTokenIssuer
from app.users.infrastructure.security.jwt_token_verifier import JwtTokenVerifier

SEGREDO = "um-segredo-de-teste-com-mais-de-32-bytes"
USUARIO = User.register(Email("ana@acme.com"), PasswordHash("hash"))


def emitir(user: User = USUARIO) -> str:
    emissor = JwtTokenIssuer(secret=SEGREDO, expires_in=timedelta(minutes=30))
    return emissor.issue(user).value


def verificador() -> TokenVerifier:
    return JwtTokenVerifier(secret=SEGREDO)


def test_aceita_o_token_que_o_emissor_gerou() -> None:
    autenticado = verificador().verify(emitir())

    assert autenticado is not None
    assert autenticado.id == USUARIO.id
    assert autenticado.role is Role.USER


def test_recusa_token_expirado() -> None:
    ha_31_minutos = datetime.now(UTC) - timedelta(minutes=31)
    emissor = JwtTokenIssuer(
        secret=SEGREDO, expires_in=timedelta(minutes=30), now=lambda: ha_31_minutos
    )

    assert verificador().verify(emissor.issue(USUARIO).value) is None


def test_recusa_token_assinado_com_outro_segredo() -> None:
    falsificador = JwtTokenIssuer(
        secret="segredo-de-quem-quer-se-passar-por-outro",
        expires_in=timedelta(minutes=30),
    )

    assert verificador().verify(falsificador.issue(USUARIO).value) is None


def test_recusa_texto_que_nao_e_token() -> None:
    assert verificador().verify("isto-nao-e-um-token") is None


def test_recusa_token_sem_assinatura() -> None:
    sem_assinatura = jwt.encode(
        {"sub": str(USUARIO.id.value), "role": "user"}, key=None, algorithm="none"
    )

    assert verificador().verify(sem_assinatura) is None


def test_recusa_token_sem_prazo_de_validade() -> None:
    eterno = jwt.encode(
        {"sub": str(USUARIO.id.value), "role": "user"}, SEGREDO, algorithm="HS256"
    )

    assert verificador().verify(eterno) is None


def assinar(claims: dict[str, object]) -> str:
    agora = datetime.now(UTC)
    completo = {"iat": agora, "exp": agora + timedelta(minutes=30), **claims}
    return jwt.encode(completo, SEGREDO, algorithm="HS256")


def test_recusa_token_cujo_dono_nao_e_um_id_valido() -> None:
    assert verificador().verify(assinar({"sub": "ana", "role": "user"})) is None


def test_recusa_token_com_papel_que_nao_existe() -> None:
    token = assinar({"sub": str(USUARIO.id.value), "role": "superuser"})

    assert verificador().verify(token) is None
