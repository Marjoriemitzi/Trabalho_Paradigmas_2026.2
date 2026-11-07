import uuid
from datetime import date

from app.finance.domain.entities.transaction import Transaction
from app.finance.domain.value_objects.category import Category
from app.finance.domain.value_objects.description import Description
from app.finance.domain.value_objects.money import Money
from app.finance.domain.value_objects.owner_id import OwnerId
from app.finance.domain.value_objects.transaction_kind import TransactionKind

DONO = OwnerId(uuid.uuid4())


def lancar() -> Transaction:
    return Transaction.record(
        owner=DONO,
        kind=TransactionKind.EXPENSE,
        amount=Money(1250),
        description=Description("Supermercado"),
        category=Category("mercado"),
        occurred_on=date(2026, 11, 7),
    )


def test_lancar_guarda_os_dados_do_lancamento() -> None:
    transacao = lancar()

    assert transacao.owner == DONO
    assert transacao.kind is TransactionKind.EXPENSE
    assert transacao.amount == Money(1250)
    assert transacao.description == Description("Supermercado")
    assert transacao.category == Category("mercado")
    assert transacao.occurred_on == date(2026, 11, 7)


def test_cada_lancamento_tem_identidade_propria() -> None:
    primeira, segunda = lancar(), lancar()

    assert primeira.id != segunda.id
    assert primeira != segunda
    assert primeira == primeira
    assert len({primeira, segunda, primeira}) == 2
