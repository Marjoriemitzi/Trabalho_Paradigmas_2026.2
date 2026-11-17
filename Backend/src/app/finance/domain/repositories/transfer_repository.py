from datetime import date
from typing import Protocol

from app.finance.domain.entities.transfer import Transfer
from app.finance.domain.value_objects.account_id import AccountId
from app.finance.domain.value_objects.owner_id import OwnerId
from app.finance.domain.value_objects.period import Period
from app.finance.domain.value_objects.transfer_flows import TransferFlows
from app.finance.domain.value_objects.transfer_id import TransferId


class TransferRepository(Protocol):
    async def add(self, transfer: Transfer) -> None: ...

    async def get(self, owner: OwnerId, transfer_id: TransferId) -> Transfer | None: ...

    async def remove(self, transfer: Transfer) -> None: ...

    async def list_between(
        self, owner: OwnerId, account: AccountId, period: Period
    ) -> list[Transfer]: ...

    async def flows_before(
        self, owner: OwnerId, account: AccountId, day: date
    ) -> TransferFlows: ...

    async def flows_by_account(
        self, owner: OwnerId
    ) -> dict[AccountId, TransferFlows]: ...
