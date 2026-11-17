from dataclasses import dataclass
from typing import Self

from app.finance.domain.value_objects.account_id import AccountId
from app.finance.domain.value_objects.account_kind import AccountKind
from app.finance.domain.value_objects.account_name import AccountName
from app.finance.domain.value_objects.owner_id import OwnerId


@dataclass(eq=False, slots=True)
class Account:
    id: AccountId
    owner: OwnerId
    name: AccountName
    kind: AccountKind

    @classmethod
    def open(cls, owner: OwnerId, name: AccountName, kind: AccountKind) -> Self:
        return cls(id=AccountId.new(), owner=owner, name=name, kind=kind)

    def __eq__(self, other: object) -> bool:
        return isinstance(other, Account) and other.id == self.id

    def __hash__(self) -> int:
        return hash(self.id)
