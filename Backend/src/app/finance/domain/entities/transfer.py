from dataclasses import dataclass
from datetime import date
from typing import Self

from app.finance.domain.exceptions import InvalidValueError
from app.finance.domain.value_objects.account_id import AccountId
from app.finance.domain.value_objects.description import Description
from app.finance.domain.value_objects.money import Money
from app.finance.domain.value_objects.owner_id import OwnerId
from app.finance.domain.value_objects.transfer_id import TransferId


@dataclass(eq=False, slots=True)
class Transfer:
    id: TransferId
    owner: OwnerId
    source: AccountId
    destination: AccountId
    amount: Money
    description: Description
    occurred_on: date

    def __post_init__(self) -> None:
        if self.source == self.destination:
            raise InvalidValueError("same_account")

    @classmethod
    def record(
        cls,
        owner: OwnerId,
        source: AccountId,
        destination: AccountId,
        amount: Money,
        description: Description,
        occurred_on: date,
    ) -> Self:
        return cls(
            id=TransferId.new(),
            owner=owner,
            source=source,
            destination=destination,
            amount=amount,
            description=description,
            occurred_on=occurred_on,
        )

    def touches(self, account: AccountId) -> bool:
        return account in (self.source, self.destination)

    def __eq__(self, other: object) -> bool:
        return isinstance(other, Transfer) and other.id == self.id

    def __hash__(self) -> int:
        return hash(self.id)
