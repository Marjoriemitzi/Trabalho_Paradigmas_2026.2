import uuid
from datetime import date

from app.finance.application.dtos.change_transaction import DeleteTransactionInput
from app.finance.application.use_cases.delete_transaction import (
    DeleteTransactionInteractor,
)
from app.finance.domain.entities.transaction import Transaction
from app.finance.domain.value_objects.account_id import AccountId
from app.finance.domain.value_objects.category import Category
from app.finance.domain.value_objects.description import Description
from app.finance.domain.value_objects.money import Money
from app.finance.domain.value_objects.owner_id import OwnerId
from app.finance.domain.value_objects.transaction_id import TransactionId
from app.finance.domain.value_objects.transaction_kind import TransactionKind
from tests.finance.fakes.change_transaction_presenter_spies import (
    DeleteTransactionPresenterSpy,
)
from tests.finance.fakes.fake_unit_of_work import FakeUnitOfWork

ANA = uuid.uuid4()


def lancamento(dono: uuid.UUID = ANA) -> Transaction:
    return Transaction.record(
        owner=OwnerId(dono),
        account=AccountId.new(),
        kind=TransactionKind.EXPENSE,
        amount=Money(4590),
        description=Description("Padaria"),
        category=Category("mercado"),
        occurred_on=date(2026, 11, 7),
    )


async def montar(
    *lancadas: Transaction,
) -> tuple[DeleteTransactionInteractor, FakeUnitOfWork, DeleteTransactionPresenterSpy]:
    uow = FakeUnitOfWork()
    for t in lancadas:
        await uow.transactions.add(t)
    presenter = DeleteTransactionPresenterSpy()
    return DeleteTransactionInteractor(uow=uow, presenter=presenter), uow, presenter


async def test_apaga_a_transacao_de_quem_pediu() -> None:
    apagada, mantida = lancamento(), lancamento()
    interactor, uow, presenter = await montar(apagada, mantida)

    await interactor.execute(DeleteTransactionInput(ANA, apagada.id.value))

    assert presenter.deleted is True
    assert uow.committed is True
    assert uow.transactions.stored == [mantida]


async def test_transacao_de_outra_pessoa_nao_e_apagada() -> None:
    da_bia = lancamento(dono=uuid.uuid4())
    interactor, uow, presenter = await montar(da_bia)

    await interactor.execute(DeleteTransactionInput(ANA, da_bia.id.value))

    assert presenter.not_found is True
    assert uow.committed is False
    assert uow.transactions.stored == [da_bia]


async def test_transacao_que_nao_existe_responde_nao_encontrada() -> None:
    interactor, _, presenter = await montar()

    await interactor.execute(DeleteTransactionInput(ANA, TransactionId.new().value))

    assert presenter.not_found is True
