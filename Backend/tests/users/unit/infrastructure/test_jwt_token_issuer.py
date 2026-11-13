from datetime import UTC, datetime, timedelta

import jwt
import pytest

from app.users.application.ports.token_issuer import TokenIssuer
from app.users.domain.entities.user import User
from app.users.domain.value_objects.email import Email
from app.users.domain.value_objects.password import PasswordHash
from app.users.infrastructure.security.jwt_token_issuer import JwtTokenIssuer

SEGREDO = "um-segredo-de-teste-com-mais-de-32-bytes"
USUARIO = User.register(Email("ana@acme.com"), PasswordHash("hash"))


def emissor() -> TokenIssuer:
    return JwtTokenIssuer(secret=SEGREDO, expires_in=timedelta(minutes=30))


def test_o_token_identifica_o_usuario() -> None:
    token = emissor().issue(USUARIO)

    claims = jwt.decode(token.value, SEGREDO, algorithms=["HS256"])

    assert claims["sub"] == str(USUARIO.id.value)


def test_expira_no_prazo_configurado() -> None:
    agora = datetime(2026, 1, 1, 12, 0, tzinfo=UTC)
    issuer = JwtTokenIssuer(
        secret=SEGREDO, expires_in=timedelta(minutes=30), now=lambda: agora
    )

    token = issuer.issue(USUARIO)

    claims = jwt.decode(
        token.value, SEGREDO, algorithms=["HS256"], options={"verify_exp": False}
    )
    assert claims["iat"] == int(agora.timestamp())
    assert claims["exp"] == int((agora + timedelta(minutes=30)).timestamp())
    assert token.expires_in == 30 * 60


def test_o_token_leva_o_papel_do_usuario() -> None:
    claims = jwt.decode(emissor().issue(USUARIO).value, SEGREDO, algorithms=["HS256"])
    assert claims["role"] == "user"


def test_o_token_nao_aparece_em_logs() -> None:
    token = emissor().issue(USUARIO)
    assert token.value not in repr(token)


def test_um_token_adulterado_nao_vale() -> None:
    token = emissor().issue(USUARIO)
    with pytest.raises(jwt.InvalidSignatureError):
        jwt.decode(
            token.value, "outro-segredo-qualquer-com-32-bytes!!", algorithms=["HS256"]
        )
