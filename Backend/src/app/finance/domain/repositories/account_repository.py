from typing import Protocol

from app.finance.domain.entities.account import Account
from app.finance.domain.value_objects.account_id import AccountId
from app.finance.domain.value_objects.owner_id import OwnerId


class AccountRepository(Protocol):
    async def add(self, account: Account) -> None: ...

    async def list_by_owner(self, owner: OwnerId) -> list[Account]: ...

    async def get(self, owner: OwnerId, account_id: AccountId) -> Account | None: ...
