import uuid
from typing import Self

from pydantic import BaseModel, ConfigDict

from app.finance.application.dtos.create_account import (
    AccountOutput,
    CreateAccountInput,
)
from app.finance.application.dtos.list_accounts import AccountSummary


class CreateAccountRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str
    kind: str

    def to_input(self, owner_id: uuid.UUID) -> CreateAccountInput:
        return CreateAccountInput(owner_id=owner_id, name=self.name, kind=self.kind)


class AccountResponse(BaseModel):
    id: str
    name: str
    kind: str

    @classmethod
    def from_output(cls, account: AccountOutput) -> Self:
        return cls(id=account.id, name=account.name, kind=account.kind)


class AccountSummaryResponse(BaseModel):
    id: str
    name: str
    kind: str
    balance_cents: int

    @classmethod
    def from_summary(cls, account: AccountSummary) -> Self:
        return cls(
            id=account.id,
            name=account.name,
            kind=account.kind,
            balance_cents=account.balance_cents,
        )


class AccountListResponse(BaseModel):
    accounts: list[AccountSummaryResponse]
