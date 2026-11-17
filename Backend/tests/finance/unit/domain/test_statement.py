import uuid
from datetime import date

import pytest

from app.finance.domain.entities.transaction import Transaction
from app.finance.domain.entities.transfer import Transfer
from app.finance.domain.exceptions import InvalidValueError
from app.finance.domain.value_objects.account_id import AccountId
from app.finance.domain.value_objects.category import Category
from app.finance.domain.value_objects.description import Description
from app.finance.domain.value_objects.money import Money
from app.finance.domain.value_objects.owner_id import OwnerId
from app.finance.domain.value_objects.period import Period
from app.finance.domain.value_objects.statement import Statement
from app.finance.domain.value_objects.totals import Totals
from app.finance.domain.value_objects.transaction_kind import TransactionKind
from app.finance.domain.value_objects.transfer_flows import TransferFlows

DONO = OwnerId(uuid.uuid4())
CONTA = AccountId(uuid.uuid4())


def lancar(kind: TransactionKind, cents: int, dia: int = 7) -> Transaction:
    return Transaction.record(
        owner=DONO,
        account=CONTA,
        kind=kind,
        amount=Money(cents),
        description=Description("Lançamento"),
        category=Category("outros"),
        occurred_on=date(2026, 11, dia),
    )


RECEITA = TransactionKind.INCOME
DESPESA = TransactionKind.EXPENSE


def test_totais_separam_o_que_entrou_do_que_saiu() -> None:
    totais = Totals.of(
        [lancar(RECEITA, 500000), lancar(DESPESA, 4590), lancar(DESPESA, 15000)]
    )

    assert totais == Totals(income_cents=500000, expense_cents=19590)
    assert totais.balance_cents == 480410


def test_saldo_negativo_quando_saiu_mais_do_que_entrou() -> None:
    assert Totals.of([lancar(DESPESA, 4590)]).balance_cents == -4590


def test_sem_lancamentos_tudo_e_zero() -> None:
    assert Totals.of([]) == Totals(income_cents=0, expense_cents=0)


def test_extrato_parte_do_saldo_anterior() -> None:
    novembro = Period(date(2026, 11, 1), date(2026, 11, 30))

    extrato = Statement(
        period=novembro,
        opening_balance_cents=100000,
        transactions=(lancar(RECEITA, 500000), lancar(DESPESA, 4590)),
    )

    assert extrato.totals == Totals(income_cents=500000, expense_cents=4590)
    assert extrato.closing_balance_cents == 100000 + 500000 - 4590


def test_extrato_so_aceita_lancamentos_do_proprio_periodo() -> None:
    so_o_dia_10 = Period(date(2026, 11, 10), date(2026, 11, 10))

    with pytest.raises(InvalidValueError) as erro:
        Statement(
            period=so_o_dia_10,
            opening_balance_cents=0,
            transactions=(lancar(DESPESA, 4590, dia=7),),
        )
    assert erro.value.problem == "transaction_outside_period"


NOVEMBRO = Period(date(2026, 11, 1), date(2026, 11, 30))
OUTRA = AccountId(uuid.uuid4())
TERCEIRA = AccountId(uuid.uuid4())


def transferir(de: AccountId, para: AccountId, cents: int, dia: int = 10) -> Transfer:
    return Transfer.record(
        owner=DONO,
        source=de,
        destination=para,
        amount=Money(cents),
        description=Description("Transferência"),
        occurred_on=date(2026, 11, dia),
    )


def test_extrato_de_uma_conta_soma_as_transferencias_no_saldo_final() -> None:
    extrato = Statement(
        period=NOVEMBRO,
        opening_balance_cents=10000,
        transactions=(lancar(DESPESA, 4590),),
        transfers=(transferir(OUTRA, CONTA, 50000), transferir(CONTA, OUTRA, 2000)),
        account=CONTA,
    )

    assert extrato.totals == Totals(income_cents=0, expense_cents=4590)
    assert extrato.transfer_flows == TransferFlows(
        incoming_cents=50000, outgoing_cents=2000
    )
    assert extrato.closing_balance_cents == 10000 - 4590 + 50000 - 2000


def test_extrato_de_todas_as_contas_nao_tem_transferencias() -> None:
    with pytest.raises(InvalidValueError) as erro:
        Statement(
            period=NOVEMBRO,
            opening_balance_cents=0,
            transactions=(),
            transfers=(transferir(OUTRA, CONTA, 100),),
        )
    assert erro.value.problem == "transfers_without_account"


def test_transferencia_que_nao_toca_a_conta_e_um_erro() -> None:
    with pytest.raises(InvalidValueError) as erro:
        Statement(
            period=NOVEMBRO,
            opening_balance_cents=0,
            transactions=(),
            transfers=(transferir(OUTRA, TERCEIRA, 100),),
            account=CONTA,
        )
    assert erro.value.problem == "transfer_of_another_account"


def test_transferencia_fora_do_periodo_e_um_erro() -> None:
    with pytest.raises(InvalidValueError) as erro:
        Statement(
            period=Period(date(2026, 11, 1), date(2026, 11, 9)),
            opening_balance_cents=0,
            transactions=(),
            transfers=(transferir(OUTRA, CONTA, 100, dia=10),),
            account=CONTA,
        )
    assert erro.value.problem == "transfer_outside_period"
