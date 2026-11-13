from datetime import date
from typing import Protocol

from app.finance.domain.entities.transaction import Transaction
from app.finance.domain.value_objects.account_id import AccountId
from app.finance.domain.value_objects.owner_id import OwnerId
from app.finance.domain.value_objects.period import Period
from app.finance.domain.value_objects.totals import Totals
from app.finance.domain.value_objects.transaction_id import TransactionId


class TransactionRepository(Protocol):
    async def add(self, transaction: Transaction) -> None: ...

    async def get(
        self, owner: OwnerId, transaction_id: TransactionId
    ) -> Transaction | None: ...

    async def update(self, transaction: Transaction) -> None: ...

    async def remove(self, transaction: Transaction) -> None: ...

    async def list_between(
        self, owner: OwnerId, period: Period, account: AccountId | None = None
    ) -> list[Transaction]: ...

    async def totals_before(
        self, owner: OwnerId, day: date, account: AccountId | None = None
    ) -> Totals: ...

    async def totals_by_account(self, owner: OwnerId) -> dict[AccountId, Totals]: ...
