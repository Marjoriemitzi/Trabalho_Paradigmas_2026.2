from datetime import date

from sqlalchemy import ColumnElement, delete, func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.finance.domain.entities.transaction import Transaction
from app.finance.domain.value_objects.account_id import AccountId
from app.finance.domain.value_objects.owner_id import OwnerId
from app.finance.domain.value_objects.period import Period
from app.finance.domain.value_objects.totals import Totals
from app.finance.domain.value_objects.transaction_id import TransactionId
from app.finance.domain.value_objects.transaction_kind import TransactionKind
from app.finance.infrastructure.persistence.mappers.transaction_mapper import (
    to_entity,
    to_model,
)
from app.finance.infrastructure.persistence.models.transaction_model import (
    TransactionModel,
)


def _soma_do_tipo(kind: TransactionKind) -> ColumnElement[int]:
    soma = func.sum(TransactionModel.amount_cents).filter(
        TransactionModel.kind == kind.value
    )
    return func.coalesce(soma, 0)


def _do_dono(owner: OwnerId, account: AccountId | None) -> list[ColumnElement[bool]]:
    condicoes = [TransactionModel.owner_id == owner.value]
    if account is not None:
        condicoes.append(TransactionModel.account_id == account.value)
    return condicoes


class SqlTransactionRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def add(self, transaction: Transaction) -> None:
        self._session.add(to_model(transaction))
        await self._session.flush()

    async def get(
        self, owner: OwnerId, transaction_id: TransactionId
    ) -> Transaction | None:
        consulta = select(TransactionModel).where(
            TransactionModel.id == transaction_id.value,
            TransactionModel.owner_id == owner.value,
        )
        modelo = await self._session.scalar(consulta)
        return None if modelo is None else to_entity(modelo)

    async def update(self, transaction: Transaction) -> None:
        novo = to_model(transaction)
        await self._session.execute(
            update(TransactionModel)
            .where(
                TransactionModel.id == transaction.id.value,
                TransactionModel.owner_id == transaction.owner.value,
            )
            .values(
                account_id=novo.account_id,
                kind=novo.kind,
                amount_cents=novo.amount_cents,
                description=novo.description,
                category=novo.category,
                occurred_on=novo.occurred_on,
            )
        )

    async def remove(self, transaction: Transaction) -> None:
        await self._session.execute(
            delete(TransactionModel).where(
                TransactionModel.id == transaction.id.value,
                TransactionModel.owner_id == transaction.owner.value,
            )
        )

    async def list_between(
        self, owner: OwnerId, period: Period, account: AccountId | None = None
    ) -> list[Transaction]:
        consulta = (
            select(TransactionModel)
            .where(
                *_do_dono(owner, account),
                TransactionModel.occurred_on.between(period.start, period.end),
            )
            .order_by(TransactionModel.occurred_on, TransactionModel.created_at)
        )
        modelos = await self._session.scalars(consulta)
        return [to_entity(modelo) for modelo in modelos]

    async def totals_before(
        self, owner: OwnerId, day: date, account: AccountId | None = None
    ) -> Totals:
        consulta = select(
            _soma_do_tipo(TransactionKind.INCOME),
            _soma_do_tipo(TransactionKind.EXPENSE),
        ).where(*_do_dono(owner, account), TransactionModel.occurred_on < day)
        entrou, saiu = (await self._session.execute(consulta)).one()
        return Totals(income_cents=int(entrou), expense_cents=int(saiu))

    async def totals_by_account(self, owner: OwnerId) -> dict[AccountId, Totals]:
        consulta = (
            select(
                TransactionModel.account_id,
                _soma_do_tipo(TransactionKind.INCOME),
                _soma_do_tipo(TransactionKind.EXPENSE),
            )
            .where(*_do_dono(owner, None))
            .group_by(TransactionModel.account_id)
        )
        linhas = await self._session.execute(consulta)
        return {
            AccountId(conta): Totals(income_cents=int(entrou), expense_cents=int(saiu))
            for conta, entrou, saiu in linhas
        }
