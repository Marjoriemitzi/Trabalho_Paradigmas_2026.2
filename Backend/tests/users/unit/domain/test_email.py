import pytest

from app.users.domain.exceptions import InvalidEmailError
from app.users.domain.value_objects.email import Email


def test_aceita_email_valido() -> None:
    assert Email("ana@acme.com").value == "ana@acme.com"


def test_normaliza_para_minusculas_sem_espacos() -> None:
    assert Email("  Ana@ACME.com ").value == "ana@acme.com"


@pytest.mark.parametrize(
    "invalido",
    ["", "ana.acme.com", "ana@", "@acme.com", "ana@acme", "ana acme@x.com"],
)
def test_recusa_email_invalido(invalido: str) -> None:
    with pytest.raises(InvalidEmailError):
        Email(invalido)


def test_dois_emails_com_mesmo_valor_sao_iguais() -> None:
    assert Email("ana@acme.com") == Email("ANA@acme.com")


def test_e_imutavel() -> None:
    email = Email("ana@acme.com")
    with pytest.raises(AttributeError):
        email.value = "outro@acme.com"  # type: ignore[misc]


def test_aceita_ate_254_caracteres_e_recusa_o_que_passa_disso() -> None:
    dominio = "@acme.com"
    no_limite = "a" * (254 - len(dominio)) + dominio
    um_a_mais = "a" + no_limite

    assert len(Email(no_limite).value) == 254
    with pytest.raises(InvalidEmailError):
        Email(um_a_mais)
