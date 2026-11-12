from typing import Protocol

from app.finance.domain.value_objects.account_id import AccountId
from app.finance.domain.value_objects.category_total import CategoryTotal
from app.finance.domain.value_objects.owner_id import OwnerId
from app.finance.domain.value_objects.period import Period
from app.finance.domain.value_objects.transaction_kind import TransactionKind


class SpendingReader(Protocol):
    async def by_category(
        self,
        owner: OwnerId,
        kind: TransactionKind,
        period: Period,
        account: AccountId | None = None,
    ) -> list[CategoryTotal]: ...
