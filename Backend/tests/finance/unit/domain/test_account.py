import uuid

import pytest

from app.finance.domain.entities.account import Account
from app.finance.domain.exceptions import InvalidValueError
from app.finance.domain.value_objects.account_kind import AccountKind
from app.finance.domain.value_objects.account_name import AccountName
from app.finance.domain.value_objects.owner_id import OwnerId

DONO = OwnerId(uuid.uuid4())


def test_nome_da_conta_perde_os_espacos_das_pontas() -> None:
    assert AccountName("  Nubank  ").text == "Nubank"


@pytest.mark.parametrize(
    ("nome", "problema"), [("   ", "blank"), ("a" * 61, "too_long")]
)
def test_nome_da_conta_recusado(nome: str, problema: str) -> None:
    with pytest.raises(InvalidValueError) as erro:
        AccountName(nome)
    assert erro.value.problem == problema


def test_nomes_que_so_mudam_maiusculas_sao_o_mesmo_nome() -> None:
    assert AccountName("Nubank").key == AccountName("  NUBANK ").key


def test_tipo_da_conta_vem_do_texto() -> None:
    assert AccountKind.parse("wallet") is AccountKind.WALLET
    assert AccountKind.parse("checking") is AccountKind.CHECKING
    assert AccountKind.parse("credit_card") is AccountKind.CREDIT_CARD
    with pytest.raises(InvalidValueError) as erro:
        AccountKind.parse("savings")
    assert erro.value.problem == "unknown"


def test_abrir_uma_conta_cria_uma_identidade_nova() -> None:
    primeira = Account.open(DONO, AccountName("Carteira"), AccountKind.WALLET)
    segunda = Account.open(DONO, AccountName("Carteira"), AccountKind.WALLET)

    assert primeira.owner == DONO
    assert primeira.name == AccountName("Carteira")
    assert primeira.kind is AccountKind.WALLET
    assert primeira != segunda
    assert len({primeira, segunda, primeira}) == 2
