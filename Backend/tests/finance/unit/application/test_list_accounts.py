import uuid
from datetime import date

from app.finance.application.dtos.list_accounts import AccountSummary, ListAccountsInput
from app.finance.application.use_cases.list_accounts import ListAccountsInteractor
from app.finance.domain.entities.account import Account
from app.finance.domain.entities.transaction import Transaction
from app.finance.domain.entities.transfer import Transfer
from app.finance.domain.value_objects.account_kind import AccountKind
from app.finance.domain.value_objects.account_name import AccountName
from app.finance.domain.value_objects.category import Category
from app.finance.domain.value_objects.description import Description
from app.finance.domain.value_objects.money import Money
from app.finance.domain.value_objects.owner_id import OwnerId
from app.finance.domain.value_objects.transaction_kind import TransactionKind
from tests.finance.fakes.fake_unit_of_work import FakeUnitOfWork
from tests.finance.fakes.list_accounts_presenter_spy import ListAccountsPresenterSpy

ANA, BIA = uuid.uuid4(), uuid.uuid4()


def conta(dono: uuid.UUID, nome: str) -> Account:
    return Account.open(OwnerId(dono), AccountName(nome), AccountKind.WALLET)


def lancamento(c: Account, kind: TransactionKind, cents: int) -> Transaction:
    return Transaction.record(
        owner=c.owner,
        account=c.id,
        kind=kind,
        amount=Money(cents),
        description=Description("Lançamento"),
        category=Category("outros"),
        occurred_on=date(2026, 11, 7),
    )


async def montar(
    *contas: Account,
    lancamentos: tuple[Transaction, ...] = (),
    transferencias: tuple[Transfer, ...] = (),
) -> tuple[ListAccountsInteractor, ListAccountsPresenterSpy]:
    uow = FakeUnitOfWork()
    for c in contas:
        await uow.accounts.add(c)
    for t in lancamentos:
        await uow.transactions.add(t)
    for tr in transferencias:
        await uow.transfers.add(tr)
    presenter = ListAccountsPresenterSpy()
    return ListAccountsInteractor(uow=uow, presenter=presenter), presenter


async def test_lista_as_contas_de_quem_pediu() -> None:
    interactor, presenter = await montar(
        conta(ANA, "Nubank"), conta(ANA, "Carteira"), conta(BIA, "Itaú")
    )

    await interactor.execute(ListAccountsInput(owner_id=ANA))

    assert presenter.accounts is not None
    assert [c.name for c in presenter.accounts] == ["Carteira", "Nubank"]


async def test_quem_nao_tem_conta_recebe_lista_vazia() -> None:
    interactor, presenter = await montar(conta(BIA, "Itaú"))

    await interactor.execute(ListAccountsInput(owner_id=ANA))

    assert presenter.accounts == ()


async def test_cada_conta_traz_o_proprio_saldo() -> None:
    nubank, carteira = conta(ANA, "Nubank"), conta(ANA, "Carteira")
    interactor, presenter = await montar(
        nubank,
        carteira,
        lancamentos=(
            lancamento(nubank, TransactionKind.INCOME, 520000),
            lancamento(nubank, TransactionKind.EXPENSE, 4590),
        ),
    )

    await interactor.execute(ListAccountsInput(owner_id=ANA))

    assert presenter.accounts == (
        AccountSummary(
            id=str(carteira.id.value), name="Carteira", kind="wallet", balance_cents=0
        ),
        AccountSummary(
            id=str(nubank.id.value),
            name="Nubank",
            kind="wallet",
            balance_cents=520000 - 4590,
        ),
    )


async def test_transferencias_mudam_o_saldo_das_duas_contas() -> None:
    corrente, cartao = conta(ANA, "Corrente"), conta(ANA, "Cartão")
    fatura = Transfer.record(
        owner=OwnerId(ANA),
        source=corrente.id,
        destination=cartao.id,
        amount=Money(150000),
        description=Description("Pagamento da fatura"),
        occurred_on=date(2026, 11, 10),
    )
    interactor, presenter = await montar(
        corrente,
        cartao,
        lancamentos=(
            lancamento(corrente, TransactionKind.INCOME, 520000),
            lancamento(cartao, TransactionKind.EXPENSE, 150000),
        ),
        transferencias=(fatura,),
    )

    await interactor.execute(ListAccountsInput(owner_id=ANA))

    assert presenter.accounts is not None
    saldos = {c.name: c.balance_cents for c in presenter.accounts}
    assert saldos == {"Cartão": 0, "Corrente": 520000 - 150000}
