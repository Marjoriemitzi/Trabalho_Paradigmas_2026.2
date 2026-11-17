import uuid
from dataclasses import replace
from datetime import date

import pytest

from app.finance.application.dtos.get_statement import (
    GetStatementInput,
    StatementEntry,
)
from app.finance.application.use_cases.get_statement import GetStatementInteractor
from app.finance.domain.entities.account import Account
from app.finance.domain.entities.transaction import Transaction
from app.finance.domain.entities.transfer import Transfer
from app.finance.domain.value_objects.account_id import AccountId
from app.finance.domain.value_objects.account_kind import AccountKind
from app.finance.domain.value_objects.account_name import AccountName
from app.finance.domain.value_objects.category import Category
from app.finance.domain.value_objects.description import Description
from app.finance.domain.value_objects.money import Money
from app.finance.domain.value_objects.owner_id import OwnerId
from app.finance.domain.value_objects.transaction_kind import TransactionKind
from tests.finance.fakes.fake_unit_of_work import FakeUnitOfWork
from tests.finance.fakes.get_statement_presenter_spy import (
    GetStatementPresenterSpy,
)

DONO = uuid.uuid4()


def conta(nome: str, dono: uuid.UUID = DONO) -> Account:
    return Account.open(OwnerId(dono), AccountName(nome), AccountKind.WALLET)


CARTEIRA, NUBANK = conta("Carteira"), conta("Nubank")
NOVEMBRO = GetStatementInput(
    owner_id=DONO, start=date(2026, 11, 1), end=date(2026, 11, 30)
)
RECEITA, DESPESA = TransactionKind.INCOME, TransactionKind.EXPENSE


def lancamento(
    dia: date,
    kind: TransactionKind,
    cents: int,
    dono: uuid.UUID = DONO,
    na: Account = CARTEIRA,
) -> Transaction:
    return Transaction.record(
        owner=OwnerId(dono),
        account=na.id,
        kind=kind,
        amount=Money(cents),
        description=Description("Lançamento"),
        category=Category("outros"),
        occurred_on=dia,
    )


async def montar(
    *lancamentos: Transaction, transferencias: tuple[Transfer, ...] = ()
) -> tuple[GetStatementInteractor, FakeUnitOfWork, GetStatementPresenterSpy]:
    uow = FakeUnitOfWork()
    for nova in (CARTEIRA, NUBANK):
        await uow.accounts.add(nova)
    for transacao in lancamentos:
        await uow.transactions.add(transacao)
    for transferencia in transferencias:
        await uow.transfers.add(transferencia)
    presenter = GetStatementPresenterSpy()
    return GetStatementInteractor(uow=uow, presenter=presenter), uow, presenter


async def test_extrato_traz_saldo_anterior_movimento_e_saldo_final() -> None:
    salario = lancamento(date(2026, 11, 5), RECEITA, 520000)
    padaria = lancamento(date(2026, 11, 7), DESPESA, 4590)
    interactor, _, presenter = await montar(
        lancamento(date(2026, 10, 20), RECEITA, 100000),
        padaria,
        salario,
    )

    await interactor.execute(NOVEMBRO)

    extrato = presenter.statement
    assert extrato is not None
    assert extrato.start == "2026-11-01"
    assert extrato.end == "2026-11-30"
    assert extrato.opening_balance_cents == 100000
    assert extrato.income_cents == 520000
    assert extrato.expense_cents == 4590
    assert extrato.closing_balance_cents == 100000 + 520000 - 4590
    assert extrato.account_id is None
    assert [e.id for e in extrato.transactions] == [
        str(salario.id.value),
        str(padaria.id.value),
    ]
    assert extrato.transactions[1] == StatementEntry(
        id=str(padaria.id.value),
        account_id=str(CARTEIRA.id.value),
        kind="expense",
        amount_cents=4590,
        description="Lançamento",
        category="outros",
        occurred_on="2026-11-07",
    )


@pytest.mark.parametrize(
    ("pedido", "problema"),
    [
        (replace(NOVEMBRO, end=date(2026, 10, 1)), "end_before_start"),
        (replace(NOVEMBRO, end=date(2027, 11, 2)), "too_long"),
    ],
)
async def test_periodo_recusado_diz_o_problema(
    pedido: GetStatementInput, problema: str
) -> None:
    interactor, _, presenter = await montar()

    await interactor.execute(pedido)

    assert presenter.invalid == ("to", problema)
    assert presenter.statement is None


async def test_o_extrato_e_so_de_quem_pediu() -> None:
    outra_pessoa = uuid.uuid4()
    interactor, _, presenter = await montar(
        lancamento(date(2026, 10, 1), RECEITA, 900000, dono=outra_pessoa),
        lancamento(date(2026, 11, 7), DESPESA, 4590, dono=outra_pessoa),
    )

    await interactor.execute(NOVEMBRO)

    assert presenter.statement is not None
    assert presenter.statement.opening_balance_cents == 0
    assert presenter.statement.transactions == ()


async def test_ler_o_extrato_nao_grava_nada() -> None:
    interactor, uow, _ = await montar()

    await interactor.execute(NOVEMBRO)

    assert uow.committed is False


async def test_o_extrato_pode_ser_de_uma_conta_so() -> None:
    padaria = lancamento(date(2026, 11, 7), DESPESA, 4590, na=CARTEIRA)
    interactor, _, presenter = await montar(
        lancamento(date(2026, 10, 20), RECEITA, 100000, na=CARTEIRA),
        lancamento(date(2026, 10, 20), RECEITA, 700000, na=NUBANK),
        padaria,
        lancamento(date(2026, 11, 8), DESPESA, 99900, na=NUBANK),
    )

    await interactor.execute(replace(NOVEMBRO, account_id=CARTEIRA.id.value))

    extrato = presenter.statement
    assert extrato is not None
    assert extrato.account_id == str(CARTEIRA.id.value)
    assert extrato.opening_balance_cents == 100000
    assert extrato.expense_cents == 4590
    assert extrato.closing_balance_cents == 100000 - 4590
    assert [e.id for e in extrato.transactions] == [str(padaria.id.value)]


@pytest.mark.parametrize(
    "pedida",
    [
        pytest.param(conta("Carteira", dono=uuid.uuid4()).id, id="de-outra-pessoa"),
        pytest.param(AccountId.new(), id="que-nao-existe"),
    ],
)
async def test_conta_que_nao_e_de_quem_pediu_nao_tem_extrato(
    pedida: AccountId,
) -> None:
    interactor, _, presenter = await montar()

    await interactor.execute(replace(NOVEMBRO, account_id=pedida.value))

    assert presenter.account_not_found is True
    assert presenter.statement is None


def transferir(de: Account, para: Account, cents: int, dia: date) -> Transfer:
    return Transfer.record(
        owner=OwnerId(DONO),
        source=de.id,
        destination=para.id,
        amount=Money(cents),
        description=Description("Transferência"),
        occurred_on=dia,
    )


async def test_o_extrato_de_uma_conta_traz_as_transferencias() -> None:
    saque = transferir(NUBANK, CARTEIRA, 20000, date(2026, 11, 10))
    interactor, _, presenter = await montar(
        lancamento(date(2026, 11, 7), DESPESA, 4590, na=CARTEIRA),
        transferencias=(
            transferir(NUBANK, CARTEIRA, 50000, date(2026, 10, 20)),
            saque,
            transferir(CARTEIRA, NUBANK, 3000, date(2026, 11, 12)),
        ),
    )

    await interactor.execute(replace(NOVEMBRO, account_id=CARTEIRA.id.value))

    extrato = presenter.statement
    assert extrato is not None
    assert extrato.opening_balance_cents == 50000
    assert extrato.transfers_in_cents == 20000
    assert extrato.transfers_out_cents == 3000
    assert extrato.closing_balance_cents == 50000 - 4590 + 20000 - 3000
    assert [t.amount_cents for t in extrato.transfers] == [20000, 3000]
    assert extrato.transfers[0].id == str(saque.id.value)


async def test_o_extrato_de_todas_as_contas_nao_traz_transferencias() -> None:
    interactor, _, presenter = await montar(
        transferencias=(
            transferir(NUBANK, CARTEIRA, 50000, date(2026, 10, 20)),
            transferir(NUBANK, CARTEIRA, 20000, date(2026, 11, 10)),
        ),
    )

    await interactor.execute(NOVEMBRO)

    extrato = presenter.statement
    assert extrato is not None
    assert extrato.opening_balance_cents == 0
    assert extrato.closing_balance_cents == 0
    assert extrato.transfers == ()
