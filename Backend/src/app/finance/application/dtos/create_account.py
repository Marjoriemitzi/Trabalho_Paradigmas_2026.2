import uuid
from dataclasses import dataclass
from typing import Self

from app.finance.domain.entities.account import Account


@dataclass(frozen=True, slots=True)
class CreateAccountInput:
    owner_id: uuid.UUID
    name: str
    kind: str


@dataclass(frozen=True, slots=True)
class AccountOutput:
    id: str
    name: str
    kind: str

    @classmethod
    def from_account(cls, account: Account) -> Self:
        return cls(
            id=str(account.id.value), name=account.name.text, kind=account.kind.value
        )
