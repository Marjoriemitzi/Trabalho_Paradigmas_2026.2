from dataclasses import dataclass

from app.finance.domain.entities.transaction import Transaction
from app.finance.domain.entities.transfer import Transfer
from app.finance.domain.exceptions import InvalidValueError
from app.finance.domain.value_objects.account_id import AccountId
from app.finance.domain.value_objects.period import Period
from app.finance.domain.value_objects.totals import Totals
from app.finance.domain.value_objects.transfer_flows import TransferFlows


@dataclass(frozen=True, slots=True)
class Statement:
    period: Period
    opening_balance_cents: int
    transactions: tuple[Transaction, ...]
    transfers: tuple[Transfer, ...] = ()
    account: AccountId | None = None

    def __post_init__(self) -> None:
        if any(not self.period.contains(t.occurred_on) for t in self.transactions):
            raise InvalidValueError("transaction_outside_period")
        if any(not self.period.contains(t.occurred_on) for t in self.transfers):
            raise InvalidValueError("transfer_outside_period")
        if self.transfers and self.account is None:
            raise InvalidValueError("transfers_without_account")
        if self.account is not None and any(
            not t.touches(self.account) for t in self.transfers
        ):
            raise InvalidValueError("transfer_of_another_account")

    @property
    def totals(self) -> Totals:
        return Totals.of(self.transactions)

    @property
    def transfer_flows(self) -> TransferFlows:
        if self.account is None:
            return TransferFlows()
        return TransferFlows.of(self.transfers, self.account)

    @property
    def closing_balance_cents(self) -> int:
        return (
            self.opening_balance_cents
            + self.totals.balance_cents
            + self.transfer_flows.net_cents
        )
