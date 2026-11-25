from datetime import date
from typing import TYPE_CHECKING

import pytest
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.finance.domain.entities.transaction import Transaction
from app.finance.domain.value_objects.account_id import AccountId
from app.finance.domain.value_objects.category import Category
from app.finance.domain.value_objects.category_total import CategoryTotal
from app.finance.domain.value_objects.description import Description
from app.finance.domain.value_objects.money import Money
from app.finance.domain.value_objects.owner_id import OwnerId
from app.finance.domain.value_objects.period import Period
from app.finance.domain.value_objects.transaction_kind import TransactionKind
from app.finance.infrastructure.persistence.models.transaction_model import (
    TransactionModel,
)
from app.finance.infrastructure.persistence.unit_of_work import SqlAlchemyUnitOfWork

if TYPE_CHECKING:
    from app.finance.application.ports.unit_of_work import UnitOfWork

Fabrica = async_sessionmaker[AsyncSession]


async def quantas_em_outra_sessao(session_factory: Fabrica) -> int:
    async with session_factory() as outra:
        total = await outra.scalar(select(func.count()).select_from(TransactionModel))
    return total or 0


async def test_commit_confirma_a_transacao(
    session_factory: Fabrica, dono: OwnerId, conta: AccountId
) -> None:
    uow: UnitOfWork = SqlAlchemyUnitOfWork(session_factory)
    async with uow:
        await uow.transactions.add(
            Transaction.record(
                owner=dono,
                account=conta,
                kind=TransactionKind.INCOME,
                amount=Money(500000),
                description=Description("Salário"),
                category=Category("salario"),
                occurred_on=date(2026, 11, 5),
            )
        )
        await uow.commit()

    assert await quantas_em_outra_sessao(session_factory) == 1


async def test_as_leituras_enxergam_o_que_foi_gravado_antes_do_commit(
    session_factory: Fabrica, dono: OwnerId, conta: AccountId
) -> None:
    uow: UnitOfWork = SqlAlchemyUnitOfWork(session_factory)
    async with uow:
        await uow.transactions.add(
            Transaction.record(
                owner=dono,
                account=conta,
                kind=TransactionKind.EXPENSE,
                amount=Money(4590),
                description=Description("Padaria"),
                category=Category("mercado"),
                occurred_on=date(2026, 11, 7),
            )
        )

        gastos = await uow.spending.by_category(
            dono, TransactionKind.EXPENSE, Period(date(2026, 11, 1), date(2026, 11, 30))
        )

    assert gastos == [CategoryTotal(Category("mercado"), 4590, 1)]
    assert await quantas_em_outra_sessao(session_factory) == 0


def padaria(dono: OwnerId, conta: AccountId) -> Transaction:
    return Transaction.record(
        owner=dono,
        account=conta,
        kind=TransactionKind.EXPENSE,
        amount=Money(4590),
        description=Description("Padaria"),
        category=Category("mercado"),
        occurred_on=date(2026, 11, 7),
    )


async def test_sem_commit_nada_fica_gravado(
    session_factory: Fabrica, dono: OwnerId, conta: AccountId
) -> None:
    uow = SqlAlchemyUnitOfWork(session_factory)
    async with uow:
        await uow.transactions.add(padaria(dono, conta))

    assert await quantas_em_outra_sessao(session_factory) == 0


async def falhar_no_meio(
    uow: SqlAlchemyUnitOfWork, dono: OwnerId, conta: AccountId
) -> None:
    async with uow:
        await uow.transactions.add(padaria(dono, conta))
        raise RuntimeError("falhou no meio do caso de uso")


async def test_erro_no_meio_desfaz_e_continua_subindo(
    session_factory: Fabrica, dono: OwnerId, conta: AccountId
) -> None:
    with pytest.raises(RuntimeError, match="falhou"):
        await falhar_no_meio(SqlAlchemyUnitOfWork(session_factory), dono, conta)

    assert await quantas_em_outra_sessao(session_factory) == 0


def test_usar_fora_do_bloco_e_um_erro_claro(session_factory: Fabrica) -> None:
    uow = SqlAlchemyUnitOfWork(session_factory)
    for repositorio in ("transactions", "accounts", "recurrences", "transfers"):
        with pytest.raises(RuntimeError, match="async with"):
            getattr(uow, repositorio)
