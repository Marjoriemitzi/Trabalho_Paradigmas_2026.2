from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.finance.domain.value_objects.account_id import AccountId
from app.finance.domain.value_objects.category import Category
from app.finance.domain.value_objects.category_total import CategoryTotal
from app.finance.domain.value_objects.owner_id import OwnerId
from app.finance.domain.value_objects.period import Period
from app.finance.domain.value_objects.transaction_kind import TransactionKind
from app.finance.infrastructure.persistence.models.transaction_model import (
    TransactionModel,
)


class SqlSpendingReader:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def by_category(
        self,
        owner: OwnerId,
        kind: TransactionKind,
        period: Period,
        account: AccountId | None = None,
    ) -> list[CategoryTotal]:
        total = func.sum(TransactionModel.amount_cents)
        consulta = (
            select(TransactionModel.category, total, func.count())
            .where(
                TransactionModel.owner_id == owner.value,
                TransactionModel.kind == kind.value,
                TransactionModel.occurred_on.between(period.start, period.end),
            )
            .group_by(TransactionModel.category)
            .order_by(total.desc(), TransactionModel.category)
        )
        if account is not None:
            consulta = consulta.where(TransactionModel.account_id == account.value)
        linhas = await self._session.execute(consulta)
        return [
            CategoryTotal(Category(categoria), int(soma), int(quantidade))
            for categoria, soma, quantidade in linhas
        ]
