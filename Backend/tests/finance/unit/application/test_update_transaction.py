import uuid
from dataclasses import replace
from datetime import date

import pytest

from app.finance.application.dtos.change_transaction import UpdateTransactionInput
from app.finance.application.dtos.transaction_warning import TransactionWarning
from app.finance.application.use_cases.update_transaction import (
    UpdateTransactionInteractor,
)
from app.finance.domain.entities.account import Account
from app.finance.domain.entities.transaction import Transaction
from app.finance.domain.value_objects.account_id import AccountId
from app.finance.domain.value_objects.account_kind import AccountKind
from app.finance.domain.value_objects.account_name import AccountName
from app.finance.domain.value_objects.category import Category
from app.finance.domain.value_objects.description import Description
from app.finance.domain.value_objects.money import Money
from app.finance.domain.value_objects.owner_id import OwnerId
from app.finance.domain.value_objects.transaction_kind import TransactionKind
from tests.finance.fakes.change_transaction_presenter_spies import (
    UpdateTransactionPresenterSpy,
)
from tests.finance.fakes.fake_categorizer import FakeCategorizer
from tests.finance.fakes.fake_transaction_check import FakeTransactionCheck
from tests.finance.fakes.fake_unit_of_work import FakeUnitOfWork

ANA = uuid.uuid4()
CARTEIRA = Account.open(OwnerId(ANA), AccountName("Carteira"), AccountKind.WALLET)
NUBANK = Account.open(OwnerId(ANA), AccountName("Nubank"), AccountKind.CHECKING)


def padaria(dono: uuid.UUID = ANA, conta: Account = CARTEIRA) -> Transaction:
    return Transaction.record(
        owner=OwnerId(dono),
        account=conta.id,
        kind=TransactionKind.EXPENSE,
        amount=Money(4590),
        description=Description("Padaria"),
        category=Category("mercado"),
        occurred_on=date(2026, 11, 7),
    )


Montagem = tuple[
    UpdateTransactionInteractor,
    FakeUnitOfWork,
    FakeCategorizer,
    UpdateTransactionPresenterSpy,
]


async def montar(
    *lancadas: Transaction, checks: tuple[FakeTransactionCheck, ...] = ()
) -> Montagem:
    uow = FakeUnitOfWork()
    for conta in (CARTEIRA, NUBANK):
        await uow.accounts.add(conta)
    for t in lancadas:
        await uow.transactions.add(t)
    categorizer = FakeCategorizer(Category("lazer"))
    presenter = UpdateTransactionPresenterSpy()
    interactor = UpdateTransactionInteractor(
        uow=uow, categorizer=categorizer, presenter=presenter, checks=checks
    )
    return interactor, uow, categorizer, presenter


def correcao(transacao: Transaction) -> UpdateTransactionInput:
    return UpdateTransactionInput(
        owner_id=ANA,
        transaction_id=transacao.id.value,
        account_id=NUBANK.id.value,
        kind="expense",
        amount_cents=4950,
        description="Padaria São Jorge",
        occurred_on=date(2026, 11, 8),
        category="mercado",
    )


async def test_correcao_grava_os_dados_novos_e_apresenta() -> None:
    original = padaria()
    interactor, uow, _, presenter = await montar(original)

    await interactor.execute(correcao(original))

    assert uow.committed is True
    [gravada] = uow.transactions.stored
    assert gravada.id == original.id
    assert gravada.account == NUBANK.id
    assert gravada.amount == Money(4950)
    assert gravada.occurred_on == date(2026, 11, 8)
    assert presenter.updated is not None
    assert presenter.updated.id == str(original.id.value)
    assert presenter.updated.amount_cents == 4950


async def test_sem_categoria_as_regras_escolhem_de_novo() -> None:
    original = padaria()
    interactor, uow, categorizer, _ = await montar(original)

    await interactor.execute(replace(correcao(original), category=None))

    [gravada] = uow.transactions.stored
    assert gravada.category == Category("lazer")
    assert categorizer.asked == [
        (TransactionKind.EXPENSE, Description("Padaria São Jorge"))
    ]


@pytest.mark.parametrize("de_quem", ["outra-pessoa", "ninguem"])
async def test_transacao_que_nao_e_de_quem_pediu_nao_e_corrigida(de_quem: str) -> None:
    da_bia = padaria(dono=uuid.uuid4())
    interactor, uow, _, presenter = await montar(da_bia)
    alvo = da_bia if de_quem == "outra-pessoa" else padaria()

    await interactor.execute(correcao(alvo))

    assert presenter.not_found is True
    assert uow.committed is False
    assert uow.transactions.stored[0].amount == Money(4590)


@pytest.mark.parametrize(
    ("mudanca", "esperado"),
    [
        ({"amount_cents": 0}, ("amount_cents", "not_positive")),
        ({"account_id": AccountId.new().value}, ("account_id", "not_found")),
        ({"category": "salario"}, ("category", "not_found")),
    ],
)
async def test_correcao_recusada_nao_muda_nada(
    mudanca: dict[str, object], esperado: tuple[str, str]
) -> None:
    original = padaria()
    interactor, uow, _, presenter = await montar(original)

    await interactor.execute(replace(correcao(original), **mudanca))  # type: ignore[arg-type]

    assert presenter.invalid == esperado
    assert uow.committed is False
    assert uow.transactions.stored[0].amount == Money(4590)


async def test_a_correcao_passa_pelas_verificacoes() -> None:
    aviso = TransactionWarning("budget_exceeded", {"category": "mercado"})
    verificacao = FakeTransactionCheck(aviso)
    original = padaria()
    interactor, _, _, presenter = await montar(original, checks=(verificacao,))

    await interactor.execute(correcao(original))

    assert [t.amount for t in verificacao.seen] == [Money(4950)]
    assert presenter.updated is not None
    assert presenter.updated.warnings == (aviso,)
