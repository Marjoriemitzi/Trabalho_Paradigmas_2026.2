from pathlib import Path

import pytest

from app.shared.infrastructure.prolog.gateway import PrologGateway
from app.users.domain.exceptions import WeakPasswordError
from app.users.domain.services.password_policy import PasswordPolicy
from app.users.infrastructure.prolog.prolog_password_policy import (
    PrologPasswordPolicy,
)

RULES_DIR = Path(__file__).resolve().parents[3] / "rules"


@pytest.fixture(scope="module")
def policy() -> PasswordPolicy:
    return PrologPasswordPolicy(PrologGateway(), RULES_DIR)


def test_aceita_senha_forte(policy: PasswordPolicy) -> None:
    policy.check("S3nha!Forte123")


def test_recusa_senha_curta(policy: PasswordPolicy) -> None:
    with pytest.raises(WeakPasswordError) as erro:
        policy.check("Ab1!")
    assert erro.value.reasons == ["too_short"]


def test_recusa_senha_sem_maiuscula(policy: PasswordPolicy) -> None:
    with pytest.raises(WeakPasswordError) as erro:
        policy.check("s3nha!forte123")
    assert erro.value.reasons == ["no_upper"]


@pytest.mark.parametrize(
    ("senha", "motivo"),
    [
        ("S3NHA!FORTE123", "no_lower"),
        ("Senha!Forte!!", "no_digit"),
        ("S3nhaForte123", "no_symbol"),
    ],
)
def test_recusa_senha_sem_cada_tipo_de_caractere(
    policy: PasswordPolicy, senha: str, motivo: str
) -> None:
    with pytest.raises(WeakPasswordError) as erro:
        policy.check(senha)
    assert erro.value.reasons == [motivo]


def test_lista_todos_os_motivos_de_uma_vez(policy: PasswordPolicy) -> None:
    with pytest.raises(WeakPasswordError) as erro:
        policy.check("abc")
    assert set(erro.value.reasons) == {"too_short", "no_upper", "no_digit", "no_symbol"}


def test_senha_vazia_e_recusada_por_ser_curta(policy: PasswordPolicy) -> None:
    with pytest.raises(WeakPasswordError) as erro:
        policy.check("")
    assert "too_short" in erro.value.reasons
