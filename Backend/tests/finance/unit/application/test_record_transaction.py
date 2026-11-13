import uuid
from dataclasses import replace
from datetime import date

import pytest

from app.finance.application.dtos.record_transaction import (
    RecordedTransaction,
    RecordTransactionInput,
)
from app.finance.application.dtos.transaction_warning import TransactionWarning
from app.finance.application.use_cases.record_transaction import (
    RecordTransactionInteractor,
)
from app.finance.domain.entities.account import Account
from app.finance.domain.value_objects.account_id import AccountId
from app.finance.domain.value_objects.account_kind import AccountKind
from app.finance.domain.value_objects.account_name import AccountName
from app.finance.domain.value_objects.category import Category
from app.finance.domain.value_objects.description import Description
from app.finance.domain.value_objects.owner_id import OwnerId
from app.finance.domain.value_objects.transaction_kind import TransactionKind
from tests.finance.fakes.fake_categorizer import FakeCategorizer
from tests.finance.fakes.fake_transaction_check import FakeTransactionCheck
from tests.finance.fakes.fake_unit_of_work import FakeUnitOfWork
from tests.finance.fakes.record_transaction_presenter_spy import (
    RecordTransactionPresenterSpy,
)

DONO = uuid.uuid4()
CARTEIRA = Account.open(OwnerId(DONO), AccountName("Carteira"), AccountKind.WALLET)


Montagem = tuple[
    RecordTransactionInteractor,
    FakeUnitOfWork,
    FakeCategorizer,
    RecordTransactionPresenterSpy,
]


async def montar(*checks: FakeTransactionCheck) -> Montagem:
    uow = FakeUnitOfWork()
    await uow.accounts.add(CARTEIRA)
    categorizer = FakeCategorizer(Category("mercado"))
    presenter = RecordTransactionPresenterSpy()
    interactor = RecordTransactionInteractor(
        uow=uow, categorizer=categorizer, presenter=presenter, checks=checks
    )
    return interactor, uow, categorizer, presenter


PEDIDO = RecordTransactionInput(
    owner_id=DONO,
    account_id=CARTEIRA.id.value,
    kind="expense",
    amount_cents=1250,
    description="Supermercado",
    occurred_on=date(2026, 11, 7),
    category="lazer",
)


async def test_lancamento_valido_e_gravado_e_apresentado() -> None:
    interactor, uow, _, presenter = await montar()

    await interactor.execute(PEDIDO)

    assert uow.committed is True
    [gravada] = uow.transactions.stored
    assert presenter.recorded == RecordedTransaction(
        id=str(gravada.id.value),
        account_id=str(CARTEIRA.id.value),
        kind="expense",
        amount_cents=1250,
        description="Supermercado",
        category="lazer",
        occurred_on="2026-11-07",
    )


async def test_sem_categoria_as_regras_escolhem_uma() -> None:
    interactor, _, categorizer, presenter = await montar()

    await interactor.execute(replace(PEDIDO, category=None))

    assert presenter.recorded is not None
    assert presenter.recorded.category == "mercado"
    assert categorizer.asked == [(TransactionKind.EXPENSE, Description("Supermercado"))]


async def test_com_categoria_as_regras_nao_sao_consultadas() -> None:
    interactor, _, categorizer, _ = await montar()

    await interactor.execute(PEDIDO)

    assert categorizer.asked == []


async def test_valor_invalido_e_recusado_sem_gravar_nada() -> None:
    interactor, uow, _, presenter = await montar()

    await interactor.execute(replace(PEDIDO, amount_cents=0))

    assert presenter.invalid == ("amount_cents", "not_positive")
    assert presenter.recorded is None
    assert uow.transactions.stored == []


@pytest.mark.parametrize(
    ("recusado", "esperado"),
    [
        (replace(PEDIDO, kind="transfer"), ("kind", "unknown")),
        (replace(PEDIDO, description="   "), ("description", "blank")),
        (replace(PEDIDO, category="lazer e cultura"), ("category", "invalid_format")),
    ],
)
async def test_cada_dado_recusado_diz_qual_campo_foi(
    recusado: RecordTransactionInput, esperado: tuple[str, str]
) -> None:
    interactor, uow, _, presenter = await montar()

    await interactor.execute(recusado)

    assert presenter.invalid == esperado
    assert uow.transactions.stored == []


async def test_a_transacao_e_de_quem_fez_o_pedido() -> None:
    interactor, uow, _, _ = await montar()

    await interactor.execute(PEDIDO)

    [gravada] = uow.transactions.stored
    assert gravada.owner == OwnerId(DONO)
    assert gravada.account == CARTEIRA.id


async def test_conta_de_outra_pessoa_e_recusada_sem_gravar_nada() -> None:
    interactor, uow, _, presenter = await montar()
    da_bia = Account.open(OwnerId(uuid.uuid4()), AccountName("Bia"), AccountKind.WALLET)
    await uow.accounts.add(da_bia)

    await interactor.execute(replace(PEDIDO, account_id=da_bia.id.value))

    assert presenter.invalid == ("account_id", "not_found")
    assert uow.transactions.stored == []


async def test_conta_que_nao_existe_e_recusada() -> None:
    interactor, uow, _, presenter = await montar()

    await interactor.execute(replace(PEDIDO, account_id=AccountId.new().value))

    assert presenter.invalid == ("account_id", "not_found")
    assert uow.transactions.stored == []


@pytest.mark.parametrize(
    "categoria", ["mercdo", "salario"], ids=["fora-da-lista", "de-outro-tipo"]
)
async def test_categoria_fora_da_lista_e_recusada_sem_gravar_nada(
    categoria: str,
) -> None:
    interactor, uow, _, presenter = await montar()

    await interactor.execute(replace(PEDIDO, category=categoria))

    assert presenter.invalid == ("category", "not_found")
    assert uow.transactions.stored == []


ESTOUROU = TransactionWarning("budget_exceeded", {"category": "lazer"})
INCOMUM = TransactionWarning("unusual_spending", {"average_cents": 300})


async def test_os_avisos_de_todas_as_verificacoes_vao_para_o_presenter() -> None:
    interactor, _, _, presenter = await montar(
        FakeTransactionCheck(ESTOUROU),
        FakeTransactionCheck(),
        FakeTransactionCheck(INCOMUM),
    )

    await interactor.execute(PEDIDO)

    assert presenter.recorded is not None
    assert presenter.recorded.warnings == (ESTOUROU, INCOMUM)


async def test_sem_verificacoes_nao_ha_avisos() -> None:
    interactor, _, _, presenter = await montar()

    await interactor.execute(PEDIDO)

    assert presenter.recorded is not None
    assert presenter.recorded.warnings == ()


async def test_a_verificacao_ve_a_transacao_ja_gravada() -> None:
    verificacao = FakeTransactionCheck()
    interactor, uow, _, _ = await montar(verificacao)

    await interactor.execute(PEDIDO)

    assert verificacao.seen == uow.transactions.stored
    assert verificacao.already_stored == [True]


@pytest.mark.parametrize(
    "recusado",
    [
        replace(PEDIDO, amount_cents=0),
        replace(PEDIDO, account_id=AccountId.new().value),
        replace(PEDIDO, category="mercdo"),
    ],
    ids=["valor", "conta", "categoria"],
)
async def test_lancamento_recusado_nao_passa_pelas_verificacoes(
    recusado: RecordTransactionInput,
) -> None:
    verificacao = FakeTransactionCheck(ESTOUROU)
    interactor, _, _, _ = await montar(verificacao)

    await interactor.execute(recusado)

    assert verificacao.seen == []
