from app.finance.domain.entities.account import Account
from app.finance.domain.exceptions import AccountNameTakenError
from app.finance.domain.value_objects.account_id import AccountId
from app.finance.domain.value_objects.owner_id import OwnerId


class FakeAccountRepository:
    def __init__(self) -> None:
        self.stored: list[Account] = []

    async def add(self, account: Account) -> None:
        if any(
            a.owner == account.owner and a.name.key == account.name.key
            for a in self.stored
        ):
            raise AccountNameTakenError(account.name.text)
        self.stored.append(account)

    async def list_by_owner(self, owner: OwnerId) -> list[Account]:
        do_dono = [a for a in self.stored if a.owner == owner]
        return sorted(do_dono, key=lambda a: a.name.key)

    async def get(self, owner: OwnerId, account_id: AccountId) -> Account | None:
        return next(
            (a for a in self.stored if a.owner == owner and a.id == account_id), None
        )
