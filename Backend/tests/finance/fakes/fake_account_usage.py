from app.finance.domain.entities.account import Account
from app.finance.domain.value_objects.owner_id import OwnerId
from tests.finance.fakes.fake_transaction_repository import FakeTransactionRepository
from tests.finance.fakes.fake_transfer_repository import FakeTransferRepository


class FakeAccountUsage:
    def __init__(
        self,
        transactions: FakeTransactionRepository,
        transfers: FakeTransferRepository,
    ) -> None:
        self._transactions = transactions
        self._transfers = transfers

    async def in_use(self, owner: OwnerId, account: Account) -> bool:
        return any(
            t.owner == owner and t.account == account.id
            for t in self._transactions.stored
        ) or any(
            t.owner == owner and t.touches(account.id) for t in self._transfers.stored
        )
