import uuid
from dataclasses import replace
from datetime import date

import pytest
from sqlalchemy import insert, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.finance.domain.entities.transaction import Transaction
from app.finance.domain.repositories.transaction_repository import (
    TransactionRepository,
)
from app.finance.domain.value_objects.account_id import AccountId
from app.finance.domain.value_objects.category import Category
from app.finance.domain.value_objects.description import Description
from app.finance.domain.value_objects.money import Money
from app.finance.domain.value_objects.owner_id import OwnerId
from app.finance.domain.value_objects.transaction_kind import TransactionKind
from app.finance.infrastructure.persistence.models.transaction_model import (
    TransactionModel,
)
from app.finance.infrastructure.persistence.repositories.sql_transaction_repository import (  # noqa: E501
    SqlTransactionRepository,
)
from tests.finance.contracts.transaction_repository_contract import (
    TransactionRepositoryContract,
)
from tests.finance.integration.conftest import NovaConta, NovoDono


class TestSqlTransactionRepository(TransactionRepositoryContract):
    @pytest.fixture
    def repository(self, session: AsyncSession) -> TransactionRepository:
        return SqlTransactionRepository(session)

    @pytest.fixture
    async def dono(self, novo_dono: NovoDono) -> OwnerId:
        return await novo_dono()

    @pytest.fixture
    async def outro_dono(self, novo_dono: NovoDono) -> OwnerId:
        return await novo_dono()

    @pytest.fixture
    async def conta(self, nova_conta: NovaConta, dono: OwnerId) -> AccountId:
        return await nova_conta(dono)

    @pytest.fixture
    async def outra_conta(self, nova_conta: NovaConta, dono: OwnerId) -> AccountId:
        return await nova_conta(dono)

    @pytest.fixture
    async def conta_do_outro(
        self, nova_conta: NovaConta, outro_dono: OwnerId
    ) -> AccountId:
        return await nova_conta(outro_dono)


def despesa(dono: OwnerId, conta: AccountId) -> Transaction:
    return Transaction.record(
        owner=dono,
        account=conta,
        kind=TransactionKind.EXPENSE,
        amount=Money(1250),
        description=Description("Supermercado"),
        category=Category("mercado"),
        occurred_on=date(2026, 11, 7),
    )


async def test_grava_cada_campo_na_sua_coluna(
    session: AsyncSession, dono: OwnerId, conta: AccountId
) -> None:
    transacao = despesa(dono, conta)
    await SqlTransactionRepository(session).add(transacao)

    linha = await session.scalar(
        select(TransactionModel).where(TransactionModel.id == transacao.id.value)
    )

    assert linha is not None
    assert linha.owner_id == dono.value
    assert linha.account_id == conta.value
    assert linha.kind == "expense"
    assert linha.amount_cents == 1250
    assert linha.description == "Supermercado"
    assert linha.category == "mercado"
    assert linha.occurred_on == date(2026, 11, 7)
    assert linha.created_at is not None


async def test_a_conta_precisa_ser_do_mesmo_dono(
    session: AsyncSession, dono: OwnerId, novo_dono: NovoDono, nova_conta: NovaConta
) -> None:
    conta_da_bia = await nova_conta(await novo_dono())

    with pytest.raises(
        IntegrityError, match="fk_transactions_account_id_owner_id_accounts"
    ):
        await SqlTransactionRepository(session).add(despesa(dono, conta_da_bia))


async def test_o_banco_recusa_categoria_fora_da_lista(
    session: AsyncSession, dono: OwnerId, conta: AccountId
) -> None:
    for categoria in ("mercdo", "salario"):
        transacao = replace(despesa(dono, conta), category=Category(categoria))

        with pytest.raises(
            IntegrityError, match="fk_transactions_kind_category_categories"
        ):
            async with session.begin_nested():
                await SqlTransactionRepository(session).add(transacao)


async def test_o_banco_recusa_valor_que_o_dominio_recusaria(
    session: AsyncSession, dono: OwnerId, conta: AccountId
) -> None:
    with pytest.raises(IntegrityError, match="ck_transactions_amount_positive"):
        await session.execute(
            insert(TransactionModel).values(
                id=uuid.uuid4(),
                owner_id=dono.value,
                account_id=conta.value,
                kind="expense",
                amount_cents=-100,
                description="Ajuste",
                category="outros",
                occurred_on=date(2026, 11, 7),
            )
        )
