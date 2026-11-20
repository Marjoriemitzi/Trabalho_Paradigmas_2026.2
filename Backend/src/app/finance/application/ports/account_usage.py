from typing import Protocol

from app.finance.domain.entities.account import Account
from app.finance.domain.value_objects.owner_id import OwnerId


class AccountUsage(Protocol):
    async def in_use(self, owner: OwnerId, account: Account) -> bool: ...
