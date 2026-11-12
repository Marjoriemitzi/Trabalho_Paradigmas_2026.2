import uuid
from dataclasses import dataclass
from typing import Self

from app.finance.domain.entities.account import Account
from app.finance.domain.value_objects.totals import Totals
from app.finance.domain.value_objects.transfer_flows import TransferFlows


@dataclass(frozen=True, slots=True)
class ListAccountsInput:
    owner_id: uuid.UUID


@dataclass(frozen=True, slots=True)
class AccountSummary:
    id: str
    name: str
    kind: str
    balance_cents: int

    @classmethod
    def from_account(
        cls, account: Account, totals: Totals, flows: TransferFlows
    ) -> Self:
        return cls(
            id=str(account.id.value),
            name=account.name.text,
            kind=account.kind.value,
            balance_cents=totals.balance_cents + flows.net_cents,
        )
