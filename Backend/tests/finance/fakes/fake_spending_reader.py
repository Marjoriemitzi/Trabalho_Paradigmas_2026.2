from app.finance.domain.value_objects.account_id import AccountId
from app.finance.domain.value_objects.category import Category
from app.finance.domain.value_objects.category_total import CategoryTotal
from app.finance.domain.value_objects.owner_id import OwnerId
from app.finance.domain.value_objects.period import Period
from app.finance.domain.value_objects.transaction_kind import TransactionKind
from tests.finance.fakes.fake_transaction_repository import FakeTransactionRepository


class FakeSpendingReader:
    def __init__(self, transactions: FakeTransactionRepository) -> None:
        self._transactions = transactions

    async def by_category(
        self,
        owner: OwnerId,
        kind: TransactionKind,
        period: Period,
        account: AccountId | None = None,
    ) -> list[CategoryTotal]:
        somas: dict[Category, tuple[int, int]] = {}
        for t in self._transactions.stored:
            if (
                t.owner == owner
                and t.kind is kind
                and period.contains(t.occurred_on)
                and (account is None or t.account == account)
            ):
                total, quantidade = somas.get(t.category, (0, 0))
                somas[t.category] = (total + t.amount.cents, quantidade + 1)
        totais = [CategoryTotal(c, total, n) for c, (total, n) in somas.items()]
        return sorted(totais, key=lambda t: (-t.total_cents, t.category.name))
