import uuid
from datetime import date

import pytest

from app.finance.domain.entities.transfer import Transfer
from app.finance.domain.exceptions import InvalidValueError
from app.finance.domain.value_objects.account_id import AccountId
from app.finance.domain.value_objects.description import Description
from app.finance.domain.value_objects.money import Money
from app.finance.domain.value_objects.owner_id import OwnerId
from app.finance.domain.value_objects.transfer_flows import TransferFlows

DONO = OwnerId(uuid.uuid4())
CORRENTE, CARTAO, CARTEIRA = AccountId.new(), AccountId.new(), AccountId.new()


def transferir(de: AccountId, para: AccountId, cents: int) -> Transfer:
    return Transfer.record(
        owner=DONO,
        source=de,
        destination=para,
        amount=Money(cents),
        description=Description("Pagamento da fatura"),
        occurred_on=date(2026, 11, 10),
    )


def test_transferencia_guarda_de_onde_e_para_onde() -> None:
    fatura = transferir(CORRENTE, CARTAO, 150000)

    assert fatura.source == CORRENTE
    assert fatura.destination == CARTAO
    assert fatura.touches(CORRENTE)
    assert fatura.touches(CARTAO)
    assert not fatura.touches(CARTEIRA)


def test_transferencia_para_a_mesma_conta_nao_existe() -> None:
    with pytest.raises(InvalidValueError) as erro:
        transferir(CORRENTE, CORRENTE, 100)
    assert erro.value.problem == "same_account"


def test_cada_transferencia_tem_identidade_propria() -> None:
    primeira, segunda = (
        transferir(CORRENTE, CARTAO, 100),
        transferir(CORRENTE, CARTAO, 100),
    )

    assert primeira != segunda
    assert len({primeira, segunda, primeira}) == 2


def test_fluxos_separam_o_que_entrou_do_que_saiu_da_conta() -> None:
    transferencias = [
        transferir(CORRENTE, CARTAO, 150000),
        transferir(CORRENTE, CARTEIRA, 20000),
        transferir(CARTEIRA, CORRENTE, 5000),
        transferir(CARTAO, CARTEIRA, 1),
    ]

    fluxos = TransferFlows.of(transferencias, CORRENTE)

    assert fluxos == TransferFlows(incoming_cents=5000, outgoing_cents=170000)
    assert fluxos.net_cents == -165000


def test_revise_troca_todos_os_campos_e_mantem_a_identidade() -> None:
    transferencia = transferir(CORRENTE, CARTAO, 1000)
    id_antes = transferencia.id

    transferencia.revise(
        source=CARTEIRA,
        destination=CORRENTE,
        amount=Money(2500),
        description=Description("Corrigida"),
        occurred_on=date(2026, 11, 20),
    )

    assert transferencia.id == id_antes
    assert transferencia.owner == DONO
    assert transferencia.source == CARTEIRA
    assert transferencia.destination == CORRENTE
    assert transferencia.amount == Money(2500)
    assert transferencia.description == Description("Corrigida")
    assert transferencia.occurred_on == date(2026, 11, 20)


def test_revise_recusa_a_mesma_conta_e_nao_muda_nada() -> None:
    transferencia = transferir(CORRENTE, CARTAO, 1000)

    with pytest.raises(InvalidValueError) as erro:
        transferencia.revise(
            source=CARTAO,
            destination=CARTAO,
            amount=Money(2500),
            description=Description("Corrigida"),
            occurred_on=date(2026, 11, 20),
        )

    assert erro.value.problem == "same_account"
    assert transferencia.source == CORRENTE
    assert transferencia.amount == Money(1000)
