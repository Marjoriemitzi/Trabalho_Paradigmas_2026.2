from collections.abc import Iterable
from dataclasses import dataclass
from typing import Self

from app.finance.domain.entities.transfer import Transfer
from app.finance.domain.value_objects.account_id import AccountId


@dataclass(frozen=True, slots=True)
class TransferFlows:
    incoming_cents: int = 0
    outgoing_cents: int = 0

    @classmethod
    def of(cls, transfers: Iterable[Transfer], account: AccountId) -> Self:
        entrou = saiu = 0
        for transferencia in transfers:
            if transferencia.destination == account:
                entrou += transferencia.amount.cents
            elif transferencia.source == account:
                saiu += transferencia.amount.cents
        return cls(incoming_cents=entrou, outgoing_cents=saiu)

    @property
    def net_cents(self) -> int:
        return self.incoming_cents - self.outgoing_cents
