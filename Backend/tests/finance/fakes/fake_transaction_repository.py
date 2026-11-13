from dataclasses import replace
from datetime import date

from app.finance.domain.entities.transaction import Transaction
from app.finance.domain.value_objects.account_id import AccountId
from app.finance.domain.value_objects.owner_id import OwnerId
from app.finance.domain.value_objects.period import Period
from app.finance.domain.value_objects.totals import Totals
from app.finance.domain.value_objects.transaction_id import TransactionId


class FakeTransactionRepository:
    def __init__(self) -> None:
        self.stored: list[Transaction] = []

    async def add(self, transaction: Transaction) -> None:
        self.stored.append(transaction)

    async def get(
        self, owner: OwnerId, transaction_id: TransactionId
    ) -> Transaction | None:
        for t in self.stored:
            if t.owner == owner and t.id == transaction_id:
                return replace(t)
        return None

    async def update(self, transaction: Transaction) -> None:
        self.stored = [transaction if t == transaction else t for t in self.stored]

    async def remove(self, transaction: Transaction) -> None:
        self.stored = [t for t in self.stored if t != transaction]

    def _do_dono(self, owner: OwnerId, account: AccountId | None) -> list[Transaction]:
        return [
            t
            for t in self.stored
            if t.owner == owner and (account is None or t.account == account)
        ]

    async def list_between(
        self, owner: OwnerId, period: Period, account: AccountId | None = None
    ) -> list[Transaction]:
        do_periodo = [
            t for t in self._do_dono(owner, account) if period.contains(t.occurred_on)
        ]
        return sorted(do_periodo, key=lambda t: t.occurred_on)

    async def totals_before(
        self, owner: OwnerId, day: date, account: AccountId | None = None
    ) -> Totals:
        return Totals.of(
            t for t in self._do_dono(owner, account) if t.occurred_on < day
        )

    async def totals_by_account(self, owner: OwnerId) -> dict[AccountId, Totals]:
        do_dono = self._do_dono(owner, None)
        contas = {t.account for t in do_dono}
        return {
            conta: Totals.of(t for t in do_dono if t.account == conta)
            for conta in contas
        }
